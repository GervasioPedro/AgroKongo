from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response, abort
from flask_login import login_required, current_user
from extensions import db
from core.models import Usuario, Safra, Produto, Transacao, Interesse, Avaliacao, Provincia, Municipio, Notificacao
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from io import BytesIO
from xhtml2pdf import pisa
from datetime import datetime
from functools import wraps
import os
from werkzeug.utils import secure_filename
import random
import string
import time

perfil_bp = Blueprint('perfil', __name__)

# --- CONFIGURAÇÃO DE UPLOADS ---
UPLOAD_FOLDER = os.path.join('core', 'static', 'uploads', 'comprovativos')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


# --- AUXILIARES E NOTIFICAÇÕES ---

def enviar_notificacao(usuario_id, titulo, mensagem, tipo='info', link=None):
    """Cria uma notificação persistente na base de dados."""
    try:
        nova_notif = Notificacao(
            usuario_id=usuario_id,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            link=link
        )
        db.session.add(nova_notif)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao enviar notificação: {e}")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def simular_chamada_api_emis(valor):
    """Simula resposta do Multicaixa Express."""
    time.sleep(0.8)
    return random.random() < 0.98


def tipo_requerido(tipo):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.tipo != tipo:
                abort(403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# --- DASHBOARDS ---

@perfil_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.tipo == 'produtor':
        return redirect(url_for('perfil.meu_perfil_produtor'))
    return redirect(url_for('perfil.meu_perfil_comprador'))


# --- DASHBOARDS ---

@perfil_bp.route('/dashboard/produtor')
@login_required
@tipo_requerido('produtor')
def meu_perfil_produtor():
    # 1. PEGAR AS SAFRAS (Stock)
    safras = Safra.query.filter_by(produtor_id=current_user.id).all()

    # 2. PEGAR OS INTERESSES (Radar de Pedidos)
    # Enviamos como 'pedidos_radar' para o loop no HTML funcionar
    pedidos_pendentes = Interesse.query.join(Safra).filter(
        Safra.produtor_id == current_user.id,
        Interesse.status == 'pendente'
    ).all()

    # 3. PEGAR AS VENDAS (Transações em curso)
    vendas_em_curso = Transacao.query.join(Safra).filter(
        Safra.produtor_id == current_user.id,
        Transacao.status.in_(['pendente_pagamento', 'aguardando_validacao', 'pago_custodia'])
    ).all()

    # 4. MÉTRICAS (Com proteção 'or 0' para evitar erro de formatação)
    total_ganho = db.session.query(func.sum(Transacao.preco_total)).join(Safra).filter(
        Safra.produtor_id == current_user.id,
        Transacao.status == 'concluido'
    ).scalar() or 0

    return render_template('perfil/dashboard_produtor.html',
                           safras=safras,
                           oportunidades=vendas_em_curso,
                           pedidos_radar=pedidos_pendentes,
                           total_ganho=total_ganho,
                           total_ativas=len(safras))


@perfil_bp.route('/dashboard/comprador')
@login_required
def meu_perfil_comprador():
    # 1. Contagem de pedidos aguardando pagamento ou validação
    # Somamos 'pendente_pagamento' (ainda não pagou) e 'aguardando_validacao' (já enviou o comprovativo)
    contagem_pendentes = Transacao.query.filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_(['pendente_pagamento', 'aguardando_validacao'])
    ).count()

    # 2. Contagem de fundos em custódia (Confirmado pelo Admin)
    contagem_custodia = Transacao.query.filter_by(
        comprador_id=current_user.id,
        status='pago_custodia'
    ).count()

    # 3. Lista de Interesses (As propostas iniciais)
    meus_interesses = Interesse.query.filter_by(
        comprador_id=current_user.id
    ).order_by(Interesse.data_criacao.desc()).all()

    # 4. Lista de Transações (As faturas e pagamentos reais)
    # Precisamos disto para o comprador clicar no botão "Pagar Agora"
    minhas_transacoes = Transacao.query.filter_by(
        comprador_id=current_user.id
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template(
        'perfil/dashboard_comprador.html',
        pedidos_pendentes_count=contagem_pendentes,
        pedidos_custodia_count=contagem_custodia,
        interesses=meus_interesses,
        transacoes=minhas_transacoes  # Enviamos a lista para a tabela
    )

# --- SISTEMA DE PAGAMENTO E CUSTÓDIA ---

@perfil_bp.route('/pagamento/<int:id>', methods=['GET', 'POST'])
@login_required
def realizar_pagamento(id):
    transacao = Transacao.query.get_or_404(id)

    # Segurança: Apenas o dono pode pagar
    if transacao.comprador_id != current_user.id:
        abort(403)

    # BLOQUEIO DE DUPLICAÇÃO: Impede pagar o que já está pago ou em validação
    if transacao.status != 'pendente_pagamento':
        flash('Esta fatura já foi submetida para pagamento ou já está validada.', 'info')
        return redirect(url_for('perfil.meu_perfil_comprador'))

    if request.method == 'POST':
        metodo = request.form.get('metodo_pagamento')

        if metodo == 'express':
            if simular_chamada_api_emis(transacao.preco_total):
                transacao.status = 'pago_custodia'
                transacao.metodo_pagamento = 'express'
                db.session.commit()

                enviar_notificacao(
                    usuario_id=transacao.safra.produtor_id,
                    titulo="Pagamento Confirmado!",
                    mensagem=f"O comprador pagou via Express (Ref: {transacao.fatura_ref}). Prossiga com a entrega.",
                    tipo="success"
                )

                flash('Pagamento via Express confirmado!', 'success')
                return redirect(url_for('perfil.meu_perfil_comprador'))

        elif metodo == 'transferencia':
            file = request.files.get('comprovativo')
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                nome_seguro = secure_filename(f"COMP_{transacao.fatura_ref}_{int(time.time())}.{ext}")

                if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
                file.save(os.path.join(UPLOAD_FOLDER, nome_seguro))

                transacao.metodo_pagamento = 'transferencia'
                transacao.comprovativo_path = nome_seguro
                transacao.status = 'aguardando_validacao'  # Status que o Admin "enxerga"
                db.session.commit()

                flash('Comprovativo enviado. Aguarde a validação administrativa.', 'info')
                return redirect(url_for('perfil.meu_perfil_comprador'))

    return render_template('perfil/pagamento.html', transacao=transacao)


@perfil_bp.route('/interesse/aceitar-pedido/<int:id>', methods=['POST'])
@login_required
def aceitar_pedido(id):
    interesse = Interesse.query.get_or_404(id)
    if interesse.safra.produtor_id != current_user.id: abort(403)

    ref = f"AK-{datetime.now().year}-{''.join(random.choices(string.digits, k=5))}"
    nova_transacao = Transacao(
        safra_id=interesse.safra_id,
        comprador_id=interesse.comprador_id,
        quantidade=interesse.quantidade_pretendida,
        preco_total=interesse.quantidade_pretendida * interesse.safra.preco_kg,
        status='pendente_pagamento',
        fatura_ref=ref
    )
    interesse.status = 'aceito'
    db.session.add(nova_transacao)
    db.session.commit()

    # Notificar Comprador para pagar
    enviar_notificacao(
        usuario_id=interesse.comprador_id,
        titulo="Pedido Aceite!",
        mensagem=f"O produtor aceitou o seu pedido de {interesse.safra.produto.nome}. Por favor, realize o pagamento.",
        tipo="info",
        link=url_for('perfil.realizar_pagamento', id=nova_transacao.id)
    )

    flash('Pedido aceite!', 'success')
    return redirect(url_for('perfil.meu_perfil_produtor'))


@perfil_bp.route('/venda/confirmar-entrega/<int:id>', methods=['POST'])
@login_required
def confirmar_entrega_final(id):
    transacao = Transacao.query.get_or_404(id)
    if transacao.safra.produtor_id != current_user.id: abort(403)
    if transacao.status != 'pago_custodia':
        flash('Pagamento ainda não garantido.', 'warning')
        return redirect(url_for('perfil.meu_perfil_produtor'))

    transacao.status = 'concluido'
    db.session.commit()

    # Notificar Comprador da Entrega
    enviar_notificacao(
        usuario_id=transacao.comprador_id,
        titulo="Produto Entregue!",
        mensagem=f"O produtor confirmou a entrega de {transacao.quantidade}kg de {transacao.safra.produto.nome}.",
        tipo="success"
    )

    flash('Venda concluída!', 'success')
    return redirect(url_for('perfil.meu_perfil_produtor'))


# --- NOTIFICAÇÕES ---

@perfil_bp.route('/notificacoes')
@login_required
def todas_notificacoes():
    notifs = Notificacao.query.filter_by(usuario_id=current_user.id).order_by(Notificacao.data_criacao.desc()).all()
    # Marcar todas como lidas ao abrir a página
    Notificacao.query.filter_by(usuario_id=current_user.id, lida=False).update({'lida': True})
    db.session.commit()
    return render_template('perfil/notificacoes.html', notificacoes=notifs)


def calcular_metricas_produtor(user_id):
    """Calcula estatísticas de desempenho para o produtor."""
    total_vendas = db.session.query(func.sum(Transacao.preco_total)) \
                       .join(Safra) \
                       .filter(Safra.produtor_id == user_id) \
                       .scalar() or 0

    safras_ativas = Safra.query.filter_by(produtor_id=user_id, status='disponivel').count()
    return total_vendas, safras_ativas



# --- CONFIGURAÇÕES DE CONTA ---

@perfil_bp.route('/definicoes', methods=['GET', 'POST'])
@login_required
def definicoes_conta():
    if request.method == 'POST':
        try:
            current_user.nome = request.form.get('nome').strip()
            current_user.telemovel = request.form.get('telemovel').strip()
            current_user.referencia = request.form.get('referencia', '').strip()
            current_user.bio = request.form.get('bio', '').strip()

            provincia_id = request.form.get('provincia_id')
            municipio_id = request.form.get('municipio_id')

            if provincia_id:
                current_user.provincia_id = int(provincia_id)
            if municipio_id:
                current_user.municipio_id = int(municipio_id)

            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('perfil.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar as definições.', 'danger')

    provincias = Provincia.query.order_by(Provincia.nome).all()
    municipios = []
    if current_user.provincia_id:
        municipios = Municipio.query.filter_by(provincia_id=current_user.provincia_id).order_by(Municipio.nome).all()

    return render_template('perfil/editar_perfil.html',
                           provincias=provincias,
                           municipios=municipios)


# --- GESTÃO DE SAFRAS (REDIRECIONAMENTOS ATUALIZADOS) ---

@perfil_bp.route('/nova-safra', methods=['GET', 'POST'])
@login_required
def nova_safra():
    if request.method == 'POST':
        try:
            nova = Safra(
                produtor_id=current_user.id,
                produto_id=int(request.form.get('produto_id')),
                quantidade_kg=float(request.form.get('quantidade_kg')),
                preco_kg=float(request.form.get('preco_kg')),
                status='disponivel'
            )
            db.session.add(nova)
            db.session.commit()
            flash('Colheita publicada com sucesso!', 'success')
            return redirect(url_for('perfil.meu_perfil_produtor'))
        except Exception:
            db.session.rollback()
            flash('Erro ao publicar. Verifique os valores.', 'danger')

    produtos = Produto.query.order_by(Produto.nome).all()
    return render_template('perfil/nova_safra.html', produtos=produtos)


@perfil_bp.route('/editar-safra/<int:id>', methods=['GET', 'POST'])
@login_required
@tipo_requerido('produtor')  # Só produtores passam aqui
def editar_safra(id):
    # SEGURANÇA: Buscamos a safra, mas garantimos que pertence ao utilizador atual
    safra = Safra.query.filter_by(id=id, produtor_id=current_user.id).first_or_404()

    # Se o filtro não encontrar nada, o first_or_404() lança um erro 404 automaticamente,
    # impedindo que um produtor veja os dados de outro.

    if request.method == 'POST':
        # ... lógica de update ...
        pass

    return render_template('perfil/editar_safra.html', safra=safra)


@perfil_bp.route('/eliminar-safra/<int:id>', methods=['POST'])
@login_required
@tipo_requerido('produtor')
def eliminar_safra(id):
    # SEGURANÇA: Só apaga se o ID da safra E o ID do produtor coincidirem
    safra = Safra.query.filter_by(id=id, produtor_id=current_user.id).first_or_404()

    try:
        db.session.delete(safra)
        db.session.commit()
        flash('Anúncio removido com sucesso!', 'success')
    except:
        db.session.rollback()
        flash('Erro ao eliminar.', 'danger')

    return redirect(url_for('perfil.meu_perfil_produtor'))


# --- FLUXO DE VENDA E STOCK ---

@perfil_bp.route('/interesse/confirmar-venda/<int:id>', methods=['POST'])
@login_required
def confirmar_venda_final(id):
    # 1. Busca segura dos dados
    interesse = Interesse.query.get_or_404(id)
    safra = interesse.safra

    # 2. Verificações de segurança (Business Logic)
    if safra.produtor_id != current_user.id:
        abort(403)  # Não é o dono da safra

    if interesse.status == 'concluido':
        flash('Esta venda já foi processada anteriormente.', 'info')
        return redirect(url_for('perfil.meu_perfil_produtor'))

    if safra.quantidade_kg < interesse.quantidade_pretendida:
        flash(f'Erro: Stock insuficiente. Disponível: {safra.quantidade_kg}kg.', 'danger')
        return redirect(url_for('perfil.meu_perfil_produtor'))

    try:
        # 3. Início da transação atómica
        venda = Transacao(
            safra_id=safra.id,
            comprador_id=interesse.comprador_id,
            quantidade=interesse.quantidade_pretendida,
            preco_total=interesse.quantidade_pretendida * safra.preco_kg,
            data_criacao=datetime.utcnow()
        )

        # Atualiza stock e status
        safra.quantidade_kg -= interesse.quantidade_pretendida
        if safra.quantidade_kg <= 0:
            safra.status = 'esgotado'

        interesse.status = 'concluido'

        db.session.add(venda)

        # 4. Gravação final
        db.session.commit()
        flash(f'Venda de {venda.quantidade}kg confirmada com sucesso!', 'success')

    except Exception as e:
        # 5. Rollback: Se algo falhar (ex: queda de luz, erro de BD), nada é alterado
        db.session.rollback()
        # Log do erro para o desenvolvedor (opcional)
        print(f"Erro ao confirmar venda: {e}")
        flash('Ocorreu um erro técnico ao processar a venda. Por favor, tente novamente.', 'danger')

    return redirect(url_for('perfil.meu_perfil_produtor'))


@perfil_bp.route('/rejeitar-venda/<int:id>', methods=['POST'])
@login_required
def rejeitar_venda(id):
    # Procuramos a transação que está em custódia
    transacao = Transacao.query.get_or_404(id)

    # Segurança: Apenas o produtor daquela safra pode rejeitar
    if transacao.safra.produtor_id != current_user.id:
        flash('Ação não autorizada.', 'danger')
        return redirect(url_for('perfil.dashboard'))

    if transacao.status == 'pago_custodia':
        # 1. Simulação de estorno financeiro
        # Aqui chamarias a API do banco ou gateway (ex: Unitel Money / EMIS)
        # processar_estorno(transacao.comprador.iban, transacao.preco_total)

        # 2. Atualizar status para o comprador saber que o dinheiro volta
        transacao.status = 'rejeitado_reembolsado'
        db.session.commit()

        flash(f'Venda rejeitada. O valor de {transacao.preco_total} Kz será devolvido ao comprador.', 'warning')
    else:
        flash('Esta transação não pode ser reembolsada neste estado.', 'info')

    return redirect(url_for('perfil.dashboard'))


import random
import string






@perfil_bp.route('/interesse/atualizar-status/<int:id>', methods=['POST'])
@login_required
def atualizar_status_interesse(id):
    interesse = Interesse.query.get_or_404(id)
    status = request.form.get('status')
    if status == 'recusado' and interesse.safra.produtor_id == current_user.id:
        interesse.status = 'recusado'
        db.session.commit()
        flash('Interesse recusado.', 'info')
    return redirect(url_for('perfil.meu_perfil_produtor'))


# --- FATURAÇÃO E PDF ---

@perfil_bp.route('/fatura/download/<int:transacao_id>')
@login_required
def baixar_fatura_pdf(transacao_id):
    transacao = Transacao.query.options(
        db.joinedload(Transacao.safra).joinedload(Safra.produtor).joinedload(Usuario.provincia),
        db.joinedload(Transacao.safra).joinedload(Safra.produtor).joinedload(Usuario.municipio),
        db.joinedload(Transacao.comprador)
    ).get_or_404(transacao_id)

    html = render_template('perfil/fatura_pdf.html', transacao=transacao)
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)

    response = make_response(pdf_buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Fatura_{transacao.id}.pdf'
    return response


# --- RELATÓRIOS E AVALIAÇÕES ---

@perfil_bp.route('/meus-relatorios')
@login_required
@tipo_requerido('produtor')
def meus_relatorios():
    # SEGURANÇA: Filtramos as transações garantindo o vínculo com o produtor logado
    transacoes = Transacao.query.join(Safra).filter(
        Safra.produtor_id == current_user.id
    ).order_by(Transacao.data_criacao.desc()).all()

    # Cálculo de métricas protegidas
    total_ganho = sum(t.preco_total for t in transacoes)
    total_vendas = len(transacoes)

    # Exemplo de lógica para gráfico (apenas deste produtor)
    # vendas_mensais = db.session.query(...)
    # .filter(Safra.produtor_id == current_user.id) ...

    return render_template('perfil/relatorios.html',
                           transacoes=transacoes,
                           total_ganho=total_ganho,
                           total_vendas=total_vendas)

@perfil_bp.route('/avaliar/<int:transacao_id>', methods=['POST'])
@login_required
def avaliar_produto(transacao_id):
    t = Transacao.query.get_or_404(transacao_id)
    if t.comprador_id != current_user.id:
        return redirect(url_for('perfil.dashboard'))

    nova = Avaliacao(
        comentario=request.form.get('comentario'),
        estrelas=int(request.form.get('estrelas')),
        safra_id=t.safra_id,
        autor_id=current_user.id
    )
    db.session.add(nova)
    db.session.commit()
    flash('Avaliação enviada!', 'success')
    return redirect(url_for('perfil.meu_perfil_comprador'))


@perfil_bp.route('/checkout/<int:interesse_id>')
@login_required
def checkout(interesse_id):
    # Procura o interesse e garante que pertence ao utilizador logado
    interesse = Interesse.query.get_or_404(interesse_id)

    if interesse.comprador_id != current_user.id:
        abort(403)

    if interesse.status != 'aceito':
        flash('Este interesse ainda não foi aceite pelo produtor.', 'warning')
        return redirect(url_for('perfil.dashboard_comprador'))

    # Cálculo do total (Pode incluir taxas de serviço aqui se necessário)
    preco_total = interesse.quantidade_pretendida * interesse.safra.preco_kg


    return render_template('perfil/pagamento.html',
                           interesse=interesse,
                           preco_total=preco_total)


# Certifique-se de que estas rotas existem aqui dentro:

@perfil_bp.route('/atividades/comprador')
@login_required
def atividades_comprador():
    # Busca transações onde o utilizador é o comprador
    atividades = Transacao.query.filter_by(comprador_id=current_user.id).order_by(Transacao.data_criacao.desc()).all()
    return render_template('perfil/atividades_comprador.html', atividades=atividades)

@perfil_bp.route('/atividades/produtor')
@login_required
def atividades_produtor():
    # Busca transações através das safras que pertencem a este produtor
    atividades = Transacao.query.join(Safra).filter(Safra.produtor_id == current_user.id).order_by(Transacao.data_criacao.desc()).all()
    return render_template('perfil/atividades_produtor.html', atividades=atividades)