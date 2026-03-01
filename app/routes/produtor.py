from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, jsonify
from flask_login import login_required, current_user
from app.models import Safra, Produto, Transacao, Notificacao, TransactionStatus, AlertaPreferencia
from app.extensions import db
from app.utils.helpers import salvar_ficheiro
from functools import wraps
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import func, case

produtor_bp = Blueprint('produtor', __name__)


# --- DECORATOR DE SEGURANÇA ---
def produtor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'produtor':
            flash("Acesso restrito a produtores validados.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)

    return decorated_function


@produtor_bp.route('/dashboard')
@login_required
@produtor_required
def dashboard():
    """Painel de Controlo Financeiro e Operacional com 4 KPIs."""

    # 1. KPIs Financeiros usando Agregação SQL (Single Hit na DB)
    # stats[0] = Receita Total (Tudo o que já foi FINALIZADO)
    # stats[1] = Em Custódia (Pago/Escrow ou Enviado/Trânsito)
    # stats[2] = A Liquidar (Mercadoria Entregue, mas ainda não transferida para o saldo disponível)
    stats = db.session.query(
        func.sum(case((Transacao.status == TransactionStatus.FINALIZADO, Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status.in_([TransactionStatus.ESCROW, TransactionStatus.ENVIADO]),
                       Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.ENTREGUE, Transacao.valor_liquido_vendedor), else_=0))
    ).filter(Transacao.vendedor_id == current_user.id).first()

    # 2. Filtros por Workflow para as abas (Tabs)
    query = Transacao.query.filter_by(vendedor_id=current_user.id)

    # Tab 1: Reservas (Aguardando aceite do produtor)
    reservas = query.filter_by(status=TransactionStatus.PENDENTE).all()

    # Tab 2: Ativas (Processamento de pagamento e Logística)
    vendas = query.filter(Transacao.status.in_([
        TransactionStatus.AGUARDANDO_PAGAMENTO,
        TransactionStatus.ANALISE,
        TransactionStatus.ESCROW,
        TransactionStatus.ENVIADO
    ])).order_by(Transacao.data_criacao.desc()).all()

    # Tab 3: Histórico (Tudo o que já saiu do fluxo operacional ativo)
    historico = query.filter(Transacao.status.in_([
        TransactionStatus.ENTREGUE,
        TransactionStatus.FINALIZADO,
        TransactionStatus.CANCELADO
    ])).order_by(Transacao.data_entrega.desc()).all()

    return render_template('painel/produtor.html',
                           receita_total=stats[0] or 0,
                           receita_pendente=stats[1] or 0,
                           receita_a_liquidar=stats[2] or 0, # Nova variável para o card azul claro/info
                           receita_disponivel=current_user.saldo_disponivel or 0,
                           reservas=reservas,
                           vendas=vendas,
                           historico=historico)


@produtor_bp.route('/api/produtor/dashboard')
@login_required
@produtor_required
def api_dashboard_produtor():
    stats = db.session.query(
        func.sum(case((Transacao.status == TransactionStatus.FINALIZADO, Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status.in_([TransactionStatus.ESCROW, TransactionStatus.ENVIADO]),
                       Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.ENTREGUE, Transacao.valor_liquido_vendedor), else_=0))
    ).filter(Transacao.vendedor_id == current_user.id).first()

    query = Transacao.query.filter_by(vendedor_id=current_user.id)

    reservas = query.filter_by(status=TransactionStatus.PENDENTE) \
        .order_by(Transacao.data_criacao.desc()).limit(20).all()

    vendas = query.filter(Transacao.status.in_([
        TransactionStatus.AGUARDANDO_PAGAMENTO,
        TransactionStatus.ANALISE,
        TransactionStatus.ESCROW,
        TransactionStatus.ENVIADO
    ])).order_by(Transacao.data_criacao.desc()).limit(20).all()

    historico = query.filter(Transacao.status.in_([
        TransactionStatus.ENTREGUE,
        TransactionStatus.FINALIZADO,
        TransactionStatus.CANCELADO
    ])).order_by(Transacao.data_criacao.desc()).limit(20).all()

    def transacao_to_dict(t: Transacao):
        return {
            'id': t.id,
            'fatura_ref': t.fatura_ref,
            'status': t.status,
            'produto': getattr(getattr(getattr(t, 'safra', None), 'produto', None), 'nome', None),
            'quantidade': float(t.quantidade_comprada) if t.quantidade_comprada is not None else None,
            'valor': float(t.valor_total_pago) if t.valor_total_pago is not None else None,
            'data': t.data_criacao.isoformat() if getattr(t, 'data_criacao', None) else None
        }

    return jsonify({
        'kpis': {
            'receita_total': float(stats[0] or 0),
            'em_custodia': float(stats[1] or 0),
            'a_liquidar': float(stats[2] or 0),
            'disponivel': float(getattr(current_user, 'saldo_disponivel', 0) or 0)
        },
        'listas': {
            'reservas': [transacao_to_dict(t) for t in reservas],
            'ativas': [transacao_to_dict(t) for t in vendas],
            'historico': [transacao_to_dict(t) for t in historico]
        },
        'perfil': {
            'conta_validada': bool(getattr(current_user, 'conta_validada', False)),
            'perfil_completo': bool(getattr(current_user, 'perfil_completo', False))
        }
    })

@produtor_bp.route('/aceitar-reserva/<int:trans_id>', methods=['POST'])
@login_required
@produtor_required
def aceitar_reserva(trans_id):
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF - validar ANTES de qualquer processamento
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    # lock_mode='update' impede que outro processo altere esta transação simultaneamente
    venda = Transacao.query.with_for_update().get_or_404(trans_id)

    if venda.vendedor_id != current_user.id:
        abort(403)

    if venda.status == TransactionStatus.PENDENTE:
        try:
            venda.status = TransactionStatus.AGUARDANDO_PAGAMENTO

            # Notificação em tempo real
            db.session.add(Notificacao(
                usuario_id=venda.comprador_id,
                mensagem=f"✅ Pedido de {venda.safra.produto.nome} aceite! Pode proceder ao pagamento.",
                link=url_for('comprador.dashboard')
            ))
            db.session.commit()
            flash('Pedido aceite! O comprador foi notificado para pagar.', 'success')
        except Exception:
            db.session.rollback()
            flash('Erro ao processar aceitação.', 'danger')

    return redirect(url_for('produtor.dashboard'))


def _criar_safra_from_form(produtor_id):
    """Cria instância de Safra a partir dos dados do formulário."""
    qtd = Decimal(request.form.get('quantidade_kg', '0').replace(',', '.'))
    preco = Decimal(request.form.get('preco_kg', '0').replace(',', '.'))
    
    imagem_file = request.files.get('imagem_safra')
    nome_foto = salvar_ficheiro(imagem_file, subpasta='safras') if imagem_file else "default_safra.webp"
    
    return Safra(
        produtor_id=produtor_id,
        produto_id=int(request.form.get('produto_id')),
        quantidade_disponivel=qtd,
        preco_por_unidade=preco,
        observacoes=request.form.get('descricao', ''),
        imagem=nome_foto
    )


def _notificar_interessados(safra):
    """Notifica utilizadores interessados na nova safra."""
    interessados = AlertaPreferencia.query.filter_by(produto_id=safra.produto_id).all()
    for alerta in interessados:
        db.session.add(Notificacao(
            usuario_id=alerta.usuario_id,
            mensagem=f"🚨 Nova safra de {safra.produto.nome} em {current_user.provincia.nome}!",
            link=url_for('mercado.detalhe_safra', id=safra.id)
        ))


@produtor_bp.route('/nova-safra', methods=['GET', 'POST'])
@login_required
@produtor_required
def nova_safra():
    if not current_user.conta_validada:
        flash('⚠️ A tua conta precisa de ser validada pela administração para publicar.', 'warning')
        return redirect(url_for('produtor.dashboard'))

    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        try:
            nova_s = _criar_safra_from_form(current_user.id)
            db.session.add(nova_s)
            db.session.flush()
            
            _notificar_interessados(nova_s)
            
            db.session.commit()
            flash('✅ Safra publicada! Interessados foram notificados.', 'success')
            return redirect(url_for('produtor.safras'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro Safra: {e}")
            flash('Erro ao publicar safra. Verifique os dados.', 'danger')

    return render_template('produtor/nova_safra.html', produtos=Produto.query.all())


@produtor_bp.route('/confirmar-envio/<int:trans_id>', methods=['POST'])
@login_required
@produtor_required
def confirmar_envio(trans_id):
    """Transição crítica: Move o estado para ENVIADO e define prazos."""
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF - validar ANTES de qualquer processamento
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)

    # Busca com bloqueio para evitar alterações simultâneas (Race Conditions)
    transacao = Transacao.query.with_for_update().get_or_404(trans_id)

    # Verificação de segurança: Só o dono da mercadoria pode confirmar o envio
    if transacao.vendedor_id != current_user.id:
        flash("Não tens permissão para gerir esta transação.", "danger")
        return redirect(url_for('produtor.dashboard'))

    # Só podemos enviar algo que já foi pago (status ESCROW)
    if transacao.status != TransactionStatus.ESCROW:
        flash("Ação inválida. O pagamento deve ser confirmado primeiro.", "warning")
        return redirect(url_for('produtor.dashboard'))

    try:
        transacao.status = TransactionStatus.ENVIADO
        transacao.data_envio = datetime.now(timezone.utc)

        # 1. Lógica de previsão (Assume-se que tens este método no teu Model)
        # Se não tiveres, podes fazer: transacao.previsao_entrega = transacao.data_envio + timedelta(days=3)
        if hasattr(transacao, 'calcular_janela_logistica'):
            transacao.calcular_janela_logistica()

        # 2. Criar Notificação para o Comprador
        previsao_str = transacao.previsao_entrega.strftime('%d/%m') if transacao.previsao_entrega else "Brevemente"

        notif = Notificacao(
            usuario_id=transacao.comprador_id,
            mensagem=f"🚚 Encomenda {transacao.fatura_ref} enviada! Previsão: {previsao_str}",
            link=url_for('comprador.dashboard')
        )
        db.session.add(notif)

        db.session.commit()
        flash(f"Envio da fatura {transacao.fatura_ref} confirmado! O comprador foi notificado.", "success")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_ENVIO_SAFRA (ID: {trans_id}): {str(e)}")
        flash("Erro interno ao processar o envio. Tenta novamente.", "danger")

    return redirect(url_for('produtor.dashboard'))

@produtor_bp.route('/safra/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@produtor_required
def editar_safra(id):
    # 1. Busca a safra garantindo que pertence ao produtor logado
    safra = Safra.query.filter_by(id=id, produtor_id=current_user.id).first_or_404()

    if request.method == 'POST':
        try:
            # 2. Atualização de Valores com Precisão Decimal
            # Substituímos o campo 'descricao' por 'observacoes' conforme o seu modelo Safra
            safra.preco_por_unidade = Decimal(request.form.get('preco', '0').replace(',', '.'))
            safra.quantidade_disponivel = Decimal(request.form.get('quantidade', '0').replace(',', '.'))
            safra.status = request.form.get('status', 'disponivel')
            safra.observacoes = request.form.get('descricao')

            # 3. Gestão Profissional de Imagem (WebP + Otimização)
            nova_imagem = request.files.get('imagem')
            if nova_imagem and nova_imagem.filename != '':
                # Usamos a função centralizada que converte para WebP e limpa o nome
                novo_nome = salvar_ficheiro(nova_imagem, subpasta='safras', privado=False)
                if novo_nome:
                    safra.imagem = novo_nome

            # 4. Persistência
            db.session.commit()
            flash('✅ Safra atualizada com sucesso!', 'success')
            return redirect(url_for('produtor.safras'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao editar safra {id}: {str(e)}")
            flash('Erro técnico ao atualizar a safra. Verifique os valores introduzidos.', 'danger')

    return render_template('produtor/editar_safra.html', safra=safra)


@produtor_bp.route('/safras')
@login_required
@produtor_required
def safras():
    safras_lista = Safra.query.filter_by(produtor_id=current_user.id).order_by(Safra.id.desc()).all()
    return render_template('produtor/safras.html', safras=safras_lista)


@produtor_bp.route('/recusar-reserva/<int:trans_id>', methods=['POST'])
@login_required
def recusar_reserva(trans_id):
    from app.models import Transacao, Notificacao
    venda = Transacao.query.get_or_404(trans_id)

    if venda.safra.produtor_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('produtor.dashboard'))

    try:
        venda.safra.quantidade_disponivel += venda.quantidade_comprada # Devolve stock
        venda.status = 'cancelada'
        db.session.commit()
        flash('Reserva recusada e stock reposto.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao cancelar.', 'danger')

    return redirect(url_for('produtor.dashboard'))


@produtor_bp.route('/confirmar-entrega/<int:trans_id>', methods=['POST'])
@login_required
@produtor_required
def confirmar_entrega(trans_id):
    venda = Transacao.query.get_or_404(trans_id)

    if venda.vendedor_id != current_user.id:
        abort(403)

    if venda.status == TransactionStatus.ESCROW:
        venda.status = TransactionStatus.ENTREGUE

        db.session.add(Notificacao(
            usuario_id=venda.comprador_id,
            mensagem=f"📦 A mercadoria {venda.fatura_ref} foi enviada. Confirme quando receber!",
            link=url_for('comprador.dashboard')
        ))
        db.session.commit()
        flash('Entrega registada!', 'success')
    return redirect(url_for('produtor.dashboard'))


@produtor_bp.route('/safra/eliminar/<int:id>', methods=['POST'])
@login_required
@produtor_required
def eliminar_safra(id):
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    safra = Safra.query.get_or_404(id)

    # 1. Verificação de Propriedade
    if safra.produtor_id != current_user.id:
        flash('Não tem permissão para eliminar esta safra.', 'danger')
        return abort(403)

    # 2. Verificação de Integridade (IMPEDE APAGAR SE HOUVER VENDAS)
    # Verifica se existem transações que não foram canceladas vinculadas a esta safra
    transacoes_ativas = Transacao.query.filter(
        Transacao.safra_id == id,
        Transacao.status != 'cancelada'
    ).first()

    if transacoes_ativas:
        flash(
            'Não é possível eliminar uma safra com pedidos ativos ou finalizados. Tente apenas atualizar o stock para 0.',
            'warning')
        return redirect(url_for('produtor.minhas_safras'))

    # 3. Eliminação
    try:
        db.session.delete(safra)
        db.session.commit()
        flash('A safra foi removida com sucesso do sistema.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao tentar eliminar a safra. Tente novamente.', 'danger')

    return redirect(url_for('produtor.safras'))

@produtor_bp.route('/vendas')
@login_required
def vendas():
    if current_user.tipo != 'produtor':
        flash("Acesso negado.", "danger")
        return redirect(url_for('main.index'))

    # 1. Filtramos todas as vendas DESTE produtor
    vendas_total = Transacao.query.filter_by(vendedor_id=current_user.id) \
        .order_by(Transacao.data_criacao.desc()).all()

    # 2. Categorizamos - ADICIONADO 'pago_escrow' nas vendas_ativas
    reservas = [v for v in vendas_total if v.status in ['reserva', 'pendente_pagamento']]

    # É aqui que o 'pago_escrow' deve estar para o produtor ver a venda após a validação do Admin
    vendas_ativas = [v for v in vendas_total if
                     v.status in ['pagamento_sob_analise', 'pago_escrow', 'enviado', 'mercadoria_enviada']]

    historico = [v for v in vendas_total if v.status in ['finalizada', 'cancelado', 'finalizada_paga']]

    return render_template('produtor/vendas.html',
                           reservas=reservas,
                           vendas=vendas_ativas,
                           historico=historico)

@produtor_bp.route('/gerar-guia/<int:trans_id>')
@login_required
def gerar_guia(trans_id):
    # 1. Busca a transação ou retorna 404 se não existir
    transacao = Transacao.query.get_or_404(trans_id)

    # 2. Segurança: Só o vendedor ou Admin podem ver
    if transacao.vendedor_id != current_user.id and getattr(current_user, 'tipo', '') != 'admin':
        flash("Acesso não autorizado.", "danger")
        return redirect(url_for('produtor.dashboard'))

    # 3. RENDERIZAÇÃO: O nome 'venda' aqui é OBRIGATÓRIO para o HTML funcionar
    return render_template('produtor/guia_remessa.html',
                           venda=transacao,
                           data_emissao=datetime.now(timezone.utc))




