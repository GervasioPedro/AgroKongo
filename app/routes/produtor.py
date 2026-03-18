from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models import Safra, Produto, Transacao, Notificacao, TransactionStatus, AlertaPreferencia, LogAuditoria, db
from app.utils.helpers import salvar_ficheiro
from functools import wraps
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from sqlalchemy import func, case

from app.utils.status_helper import status_to_value

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
    
    # Garantir que temos os dados mais recentes do usuário
    db.session.refresh(current_user)

    # 1. KPIs Financeiros usando Agregação SQL (Single Hit na DB)
    stats = db.session.query(
        # Receita Total: Transações FINALIZADAS (dinheiro já recebido)
        func.sum(case((Transacao.status == status_to_value(TransactionStatus.FINALIZADO), Transacao.valor_liquido_vendedor), else_=0)),
        # Valor em Custódia: ESCROW + ENVIADO (pagamento confirmado, mercadoria a caminho)
        func.sum(case((Transacao.status.in_([status_to_value(TransactionStatus.ESCROW), 
                                              status_to_value(TransactionStatus.ENVIADO)]),
                       Transacao.valor_liquido_vendedor), else_=0)),
        # A Liquidar: ENTREGUE (mercadoria chegou, aguardando confirmação final)
        func.sum(case((Transacao.status == status_to_value(TransactionStatus.ENTREGUE), Transacao.valor_liquido_vendedor), else_=0))
    ).filter(Transacao.vendedor_id == current_user.id).first()

    # 2. Filtros por Workflow para as abas (Tabs)
    query = Transacao.query.filter_by(vendedor_id=current_user.id)

    # Tab 1: Reservas (Aguardando aceite do produtor)
    reservas = query.filter_by(status=status_to_value(TransactionStatus.PENDENTE)).order_by(Transacao.data_criacao.desc()).all()

    # Tab 2: Ativas (Processamento de pagamento e Logística)
    vendas = query.filter(Transacao.status.in_([
        status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO),
        status_to_value(TransactionStatus.ANALISE),
        status_to_value(TransactionStatus.ESCROW),
        status_to_value(TransactionStatus.ENVIADO)
    ])).order_by(Transacao.data_criacao.desc()).all()

    # Tab 3: Histórico (Tudo o que já saiu do fluxo operacional ativo)
    historico = query.filter(Transacao.status.in_([
        status_to_value(TransactionStatus.ENTREGUE),
        status_to_value(TransactionStatus.FINALIZADO),
        status_to_value(TransactionStatus.CANCELADO),
        status_to_value(TransactionStatus.DISPUTA)
    ])).order_by(Transacao.data_criacao.desc()).all()

    return render_template('painel/produtor.html',
                           receita_total=stats[0] or 0,
                           receita_pendente=stats[1] or 0,
                           receita_a_liquidar=stats[2] or 0, 
                           receita_disponivel=current_user.saldo_disponivel or 0,
                           reservas=reservas,
                           vendas=vendas,
                           historico=historico)

@produtor_bp.route('/aceitar-reserva/<int:trans_id>', methods=['POST'])
@login_required
@produtor_required
def aceitar_reserva(trans_id):
    try:
        # lock_mode='update' impede que outro processo altere esta transação simultaneamente
        venda = Transacao.query.with_for_update().get_or_404(trans_id)

        if venda.vendedor_id != current_user.id:
            abort(403)

        if venda.status == status_to_value(TransactionStatus.PENDENTE):
            # Usa o método centralizado para registar histórico
            venda.mudar_status(status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO), "Aceite pelo produtor")

            # Notificação em tempo real
            db.session.add(Notificacao(
                usuario_id=venda.comprador_id,
                mensagem=f"✅ Pedido {venda.fatura_ref} aceite! Pode proceder ao pagamento.",
                link=url_for('comprador.dashboard') # Link genérico se não houver detalhe específico
            ))
            
            # Log Auditoria
            db.session.add(LogAuditoria(
                usuario_id=current_user.id, 
                acao="VENDA_ACEITE", 
                detalhes=f"Ref: {venda.fatura_ref}",
                ip=request.remote_addr
            ))
            
            db.session.commit()
            flash('Pedido aceite! O comprador foi notificado para pagar.', 'success')
        else:
             flash('Esta reserva já não está pendente.', 'warning')
             
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao aceitar reserva {trans_id}: {e}")
        flash('Erro técnico ao processar aceitação.', 'danger')

    return redirect(url_for('produtor.dashboard'))


@produtor_bp.route('/nova-safra', methods=['GET', 'POST'])
@login_required
@produtor_required
def nova_safra():
    if not current_user.conta_validada:
        flash('⚠️ A tua conta precisa de ser validada pela administração para publicar.', 'warning')
        return redirect(url_for('produtor.dashboard'))

    if request.method == 'POST':
        try:
            # Captura com sanitização
            try:
                qtd = Decimal(request.form.get('quantidade_kg', '0').replace(',', '.'))
                preco = Decimal(request.form.get('preco_kg', '0').replace(',', '.'))
            except InvalidOperation:
                flash('Valores de quantidade ou preço inválidos.', 'danger')
                return redirect(url_for('produtor.nova_safra'))
                
            if qtd <= 0 or preco <= 0:
                 flash('Quantidade e preço devem ser maiores que zero.', 'warning')
                 return redirect(url_for('produtor.nova_safra'))

            imagem_file = request.files.get('imagem_safra')
            nome_foto = salvar_ficheiro(imagem_file, subpasta='safras') if imagem_file else "default_safra.webp"

            nova_s = Safra(
                produtor_id=current_user.id,
                produto_id=int(request.form.get('produto_id')),
                quantidade_disponivel=qtd,
                preco_por_unidade=preco,
                observacoes=request.form.get('descricao', ''),
                imagem=nome_foto
            )
            db.session.add(nova_s)
            db.session.flush()  # Gera o ID da safra antes do commit final

            # --- MOTOR DE ALERTAS (Background-ready) ---
            interessados = AlertaPreferencia.query.filter_by(produto_id=nova_s.produto_id).all()
            for alerta in interessados:
                # Evitar notificar o próprio produtor se ele tiver alerta (pouco provável mas possível)
                if alerta.usuario_id != current_user.id:
                    db.session.add(Notificacao(
                        usuario_id=alerta.usuario_id,
                        mensagem=f"🚨 Nova safra de {nova_s.produto.nome} em {current_user.provincia.nome}!",
                        link=url_for('mercado.detalhes_safra', id=nova_s.id)
                    ))
            
            db.session.add(LogAuditoria(
                usuario_id=current_user.id,
                acao="SAFRA_CRIADA",
                detalhes=f"ID: {nova_s.id} | Produto: {nova_s.produto_id} | Qtd: {qtd}",
                ip=request.remote_addr
            ))

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

    try:
        # Busca com bloqueio para evitar alterações simultâneas (Race Conditions)
        transacao = Transacao.query.with_for_update().get_or_404(trans_id)

        # Verificação de segurança: Só o dono da mercadoria pode confirmar o envio
        if transacao.vendedor_id != current_user.id:
            abort(403)

        # Só podemos enviar algo que já foi pago (status ESCROW)
        if transacao.status != status_to_value(TransactionStatus.ESCROW):
            flash("Ação inválida. O pagamento deve ser confirmado primeiro.", "warning")
            return redirect(url_for('produtor.dashboard'))

        transacao.mudar_status(status_to_value(TransactionStatus.ENVIADO), "Mercadoria enviada pelo produtor.")
        transacao.data_envio = datetime.now(timezone.utc)

        # 1. Lógica de previsão
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
        
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="VENDA_ENVIADA",
            detalhes=f"Ref: {transacao.fatura_ref}",
            ip=request.remote_addr
        ))

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
                    # Opcional: Apagar imagem antiga se não for default
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
@produtor_required
def recusar_reserva(trans_id):
    try:
        venda = Transacao.query.with_for_update().get_or_404(trans_id)

        if venda.vendedor_id != current_user.id:
            abort(403)
            
        if venda.status != status_to_value(TransactionStatus.PENDENTE):
             flash('Só é possível recusar reservas pendentes.', 'warning')
             return redirect(url_for('produtor.dashboard'))

        # Devolve stock
        if venda.safra:
             venda.safra.quantidade_disponivel += venda.quantidade_comprada
        
        venda.mudar_status(status_to_value(TransactionStatus.CANCELADO), "Recusada pelo produtor")
        
        db.session.add(Notificacao(
            usuario_id=venda.comprador_id,
            mensagem=f"❌ O seu pedido {venda.fatura_ref} foi recusado pelo produtor.",
            link=url_for('comprador.dashboard')
        ))
        
        db.session.commit()
        flash('Reserva recusada e stock reposto.', 'info')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao recusar reserva {trans_id}: {e}")
        flash('Erro técnico ao cancelar reserva.', 'danger')

    return redirect(url_for('produtor.dashboard'))


# NOTA: O produtor NÃO deve confirmar a entrega. Quem confirma é o COMPRADOR.
# A rota 'confirmar_entrega' foi removida ou deve ser movida para o comprador_bp.
# Mantive a lógica abaixo apenas se for um caso especial de "auto-confirmação" admin, 
# mas num marketplace seguro, o vendedor nunca confirma que entregou para receber o dinheiro.
# VOU COMENTAR PARA SEGURANÇA.

# @produtor_bp.route('/confirmar-entrega/<int:trans_id>', methods=['POST'])
# ... (Lógica perigosa removida)


@produtor_bp.route('/safra/eliminar/<int:id>', methods=['POST'])
@login_required
@produtor_required
def eliminar_safra(id):
    safra = Safra.query.get_or_404(id)

    # 1. Verificação de Propriedade
    if safra.produtor_id != current_user.id:
        flash('Não tem permissão para eliminar esta safra.', 'danger')
        return abort(403)

    # 2. Verificação de Integridade (IMPEDE APAGAR SE HOUVER VENDAS)
    # Verifica se existem transações que não foram canceladas vinculadas a esta safra
    transacoes_ativas = Transacao.query.filter(
        Transacao.safra_id == id,
        Transacao.status != status_to_value(TransactionStatus.CANCELADO)
    ).first()

    if transacoes_ativas:
        flash(
            'Não é possível eliminar uma safra com pedidos ativos ou finalizados. Tente apenas atualizar o stock para 0.',
            'warning')
        return redirect(url_for('produtor.safras')) # Corrigido redirect

    # 3. Eliminação
    try:
        db.session.delete(safra)
        db.session.commit()
        flash('A safra foi removida com sucesso do sistema.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro eliminar safra {id}: {e}")
        flash('Erro ao tentar eliminar a safra. Tente novamente.', 'danger')

    return redirect(url_for('produtor.safras'))


@produtor_bp.route('/vendas')
@login_required
@produtor_required
def vendas():
    # 1. Filtramos todas as vendas DESTE produtor
    vendas_total = Transacao.query.filter_by(vendedor_id=current_user.id) \
        .order_by(Transacao.data_criacao.desc()).all()

    # 2. Categorizamos
    reservas = [v for v in vendas_total if v.status in [status_to_value(TransactionStatus.PENDENTE), status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO)]]

    vendas_ativas = [v for v in vendas_total if
                     v.status in [status_to_value(TransactionStatus.ANALISE), status_to_value(TransactionStatus.ESCROW), status_to_value(TransactionStatus.ENVIADO)]]

    historico = [v for v in vendas_total if v.status in [status_to_value(TransactionStatus.FINALIZADO), status_to_value(TransactionStatus.CANCELADO), status_to_value(TransactionStatus.DISPUTA), status_to_value(TransactionStatus.ENTREGUE)]]

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

    # 3. RENDERIZAÇÃO
    return render_template('produtor/guia_remessa.html',
                           venda=transacao,
                           data_emissao=datetime.now())