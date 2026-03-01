# app/routes/comprador_v2.py - Versão com UUID e processamento assíncrono
import hashlib
import base64
import qrcode
from io import BytesIO
from datetime import datetime, timezone
from decimal import Decimal

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, abort, make_response
)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models import (
    Transacao, Safra, Usuario, LogAuditoria,
    HistoricoStatus, Notificacao, Avaliacao, TransactionStatus
)
from app.utils.helpers import salvar_ficheiro
from app.tasks.pagamentos import processar_liquidacao

comprador_bp = Blueprint('comprador', __name__)


@comprador_bp.route('/confirmar-recebimento/<string:trans_uuid>', methods=['POST'])
@login_required
def confirmar_recebimento(trans_uuid):
    """
    Confirmação de recebimento com UUID e processamento assíncrono.
    UX: Resposta imediata + processamento em background.
    Segurança: UUID v4 protege contra enumeração de IDs.
    """
    
    # 1. Buscar transação por UUID (proteção contra enumeração)
    transacao = Transacao.query.filter_by(uuid=trans_uuid).with_for_update().first_or_404()
    
    # 2. Segurança: Apenas o comprador dono pode confirmar
    if transacao.comprador_id != current_user.id:
        abort(403)
    
    # 3. Validação de estado
    if transacao.status != TransactionStatus.ENVIADO:
        flash("Esta encomenda não está em estado de receção.", "warning")
        return redirect(url_for('comprador.dashboard'))
    
    try:
        # 4. Atualização imediata do estado (UX rápida)
        transacao.status = TransactionStatus.ENTREGUE
        transacao.data_entrega = datetime.now(timezone.utc)
        
        # 5. Disparar task assíncrona para processamento financeiro
        task = processar_liquidacao.delay(transacao.id)
        
        # 6. Log de auditoria
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="CONFIRMACAO_RECEBIMENTO",
            detalhes=f"Usuário confirmou recebimento da transação {transacao.fatura_ref}. Task {task.id} disparada."
        ))
        
        # 7. Notificação imediata ao produtor
        db.session.add(Notificacao(
            usuario_id=transacao.vendedor_id,
            mensagem=f"📦 Recebimento confirmado! {transacao.fatura_ref} em processamento financeiro.",
            link=url_for('produtor.vendas')
        ))
        
        db.session.commit()
        
        # 8. UX: Resposta imediata ao usuário
        flash("✅ Sucesso! Estamos a processar a transferência para o produtor em segundo plano.", "success")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_RECEBIMENTO_UUID {trans_uuid}: {e}")
        flash("Erro ao processar a confirmação. Tente novamente.", "danger")
    
    return redirect(url_for('comprador.dashboard'))


# Mantém as outras rotas existentes...
@comprador_bp.route('/dashboard')
@login_required
def dashboard():
    """Painel do Comprador com métricas reais."""

    # 1. Consultas Base (Filtradas pelo utilizador atual)
    query = Transacao.query.filter_by(comprador_id=current_user.id)

    # 2. Categorização para as Tabs
    # Tab 1: Aguardando Ações (Pendente de aceite ou Pagamento)
    pendentes = query.filter(Transacao.status.in_([
        TransactionStatus.PENDENTE,
        TransactionStatus.AGUARDANDO_PAGAMENTO
    ])).all()

    # Tab 2: Em Trânsito (Pago, Em Análise ou Enviado)
    em_transito = query.filter(Transacao.status.in_([
        TransactionStatus.ANALISE,
        TransactionStatus.ESCROW,
        TransactionStatus.ENVIADO
    ])).order_by(Transacao.data_envio.desc()).all()

    # Tab 3: Histórico (Entregue, Finalizada ou Cancelada)
    historico = query.filter(Transacao.status.in_([
        TransactionStatus.ENTREGUE,
        TransactionStatus.FINALIZADO,
        TransactionStatus.CANCELADO
    ])).order_by(Transacao.data_entrega.desc()).all()

    # 3. KPIs do Comprador
    total_gasto = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_([TransactionStatus.ENTREGUE, TransactionStatus.FINALIZADO])
    ).scalar() or 0

    compras_ativas = query.filter(Transacao.status != TransactionStatus.FINALIZADO).count()

    return render_template('painel/comprador.html',
                           pendentes=pendentes,
                           em_transito=em_transito,
                           historico=historico,
                           total_gasto=total_gasto,
                           compras_ativas=compras_ativas)
