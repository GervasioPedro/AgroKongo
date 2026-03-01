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
    HistoricoStatus, Notificacao, TransactionStatus
)
from app.utils.helpers import salvar_ficheiro

comprador_bp = Blueprint('comprador', __name__)


# --- DASHBOARD CENTRALIZADO ---
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


# --- GESTÃO DE RESERVAS (ANTES DO PAGAMENTO) ---
@comprador_bp.route('/minhas-reservas')
@login_required
def minhas_reservas():
    """Lista apenas o que precisa de ação imediata (confirmar stock ou pagar)."""
    transacoes = Transacao.query.filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_([TransactionStatus.PENDENTE, TransactionStatus.AGUARDANDO_PAGAMENTO])
    ).order_by(Transacao.data_criacao.desc()).all()
    return render_template('comprador/minhas_reservas.html', transacoes=transacoes)


@comprador_bp.route('/pagar-reserva/<int:trans_id>')
@login_required
def pagar_reserva(trans_id):
    """Página com o IBAN da AgroKongo e formulário de upload."""
    venda = Transacao.query.get_or_404(trans_id)

    if venda.comprador_id != current_user.id:
        abort(403)

    if venda.status == TransactionStatus.PENDENTE:
        flash("Aguarde a confirmação de stock pelo produtor antes de pagar.", "warning")
        return redirect(url_for('comprador.minhas_reservas'))

    if venda.status != TransactionStatus.AGUARDANDO_PAGAMENTO:
        flash("Esta transação já não se encontra em fase de pagamento.", "info")
        return redirect(url_for('comprador.minhas_compras'))

    return render_template('comprador/pagar_reserva.html', transacao=venda)


@comprador_bp.route('/submeter-comprovativo/<int:trans_id>', methods=['POST'])
@login_required
def submeter_comprovativo(trans_id):
    """Único ponto de entrada para talões bancários."""
    venda = Transacao.query.with_for_update().get_or_404(trans_id)

    if venda.comprador_id != current_user.id:
        abort(403)

    ficheiro = request.files.get('comprovativo')
    if not ficheiro:
        flash("Por favor, selecione o ficheiro do comprovativo.", "warning")
        return redirect(url_for('comprador.pagar_reserva', trans_id=trans_id))

    try:
        nome_foto = salvar_ficheiro(ficheiro, subpasta='comprovativos', privado=True)

        status_anterior = venda.status
        venda.comprovativo_path = nome_foto
        venda.status = TransactionStatus.ANALISE

        db.session.add(HistoricoStatus(
            transacao_id=venda.id,
            status_anterior=status_anterior,
            status_novo=TransactionStatus.ANALISE,
            observacao="Talão submetido via dashboard do comprador."
        ))

        db.session.commit()
        flash("Talão enviado! O Admin validará o pagamento em breve.", "success")
        return redirect(url_for('comprador.minhas_compras'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no upload: {e}")
        flash("Erro técnico ao processar ficheiro.", "danger")
        return redirect(url_for('comprador.pagar_reserva', trans_id=trans_id))


# --- GESTÃO DE COMPRAS ATIVAS (PÓS-PAGAMENTO) ---
@comprador_bp.route('/minhas-compras')
@login_required
def minhas_compras():
    """Acompanhamento de logística e entregas."""
    status_compras = [
        TransactionStatus.ANALISE, TransactionStatus.ESCROW,
        TransactionStatus.ENVIADO, TransactionStatus.ENTREGUE,
        TransactionStatus.FINALIZADO, TransactionStatus.DISPUTA
    ]
    compras = Transacao.query.filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_(status_compras)
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('comprador/minhas_compras.html', compras=compras)


@comprador_bp.route('/confirmar-recebimento/<int:trans_id>', methods=['POST'])
@login_required
def confirmar_recebimento(trans_id):
    """O comprador confirma a chegada da mercadoria e liberta o pagamento."""

    # Locking para evitar cliques duplos que processariam o saldo duas vezes
    transacao = Transacao.query.with_for_update().get_or_404(trans_id)

    # Segurança: Apenas o comprador dono da transação pode confirmar
    if transacao.comprador_id != current_user.id:
        abort(403)

    # Só se pode confirmar o que foi enviado e ainda não foi finalizado
    if transacao.status != TransactionStatus.ENVIADO:
        flash("Esta encomenda não está em estado de receção.", "warning")
        return redirect(url_for('comprador.dashboard'))

    try:
        transacao.status = TransactionStatus.ENTREGUE
        transacao.data_entrega = datetime.now(timezone.utc)

        # Libertar apenas o valor líquido (Total - Comissão)
        vendedor = transacao.vendedor

        # Garantimos que o cálculo decimal é seguro
        valor_a_pagar = Decimal(str(transacao.valor_liquido_vendedor))
        vendedor.saldo_disponivel = (vendedor.saldo_disponivel or 0) + valor_a_pagar

        # Notificar o Produtor
        db.session.add(Notificacao(
            usuario_id=vendedor.id,
            mensagem=f"💰 Saldo libertado! Recebeste o pagamento da fatura {transacao.fatura_ref}.",
            link=url_for('produtor.vendas')
        ))

        db.session.commit()
        flash("Recebimento confirmado! O saldo foi libertado para o produtor.", "success")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_RECEBIMENTO: {e}")
        flash("Erro ao processar a confirmação.", "danger")

    return redirect(url_for('comprador.dashboard'))

@comprador_bp.route('/avaliar/<int:trans_id>', methods=['POST'])
@login_required
def avaliar_venda(trans_id):
    venda = Transacao.query.get_or_404(trans_id)
    if venda.comprador_id != current_user.id:
        flash("Ação não permitida.", "danger")
        return redirect(url_for('comprador.minhas_compras'))

    try:
        estrelas = int(request.form.get('estrelas', 5))
        nova_av = Avaliacao(
            transacao_id=venda.id,
            produtor_id=venda.vendedor_id,
            comprador_id=current_user.id,
            estrelas=estrelas,
            comentario=request.form.get('comentario')
        )
        db.session.add(nova_av)
        db.session.add(Notificacao(
            usuario_id=venda.vendedor_id,
            mensagem=f"⭐ Recebeste {estrelas} estrelas na venda {venda.fatura_ref}!"
        ))
        db.session.commit()
        flash("Obrigado pela sua avaliação!", "success")
    except:
        db.session.rollback()
        flash("Erro ao submeter avaliação.", "danger")

    return redirect(url_for('comprador.minhas_compras'))


@comprador_bp.route('/abrir-disputa/<int:trans_id>', methods=['POST'])
@login_required
def abrir_disputa(trans_id):
    venda = Transacao.query.with_for_update().get_or_404(trans_id)
    if venda.comprador_id != current_user.id: abort(403)

    if not venda.transferencia_concluida:
        venda.status = TransactionStatus.DISPUTA
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="DISPUTA",
            detalhes=f"Disputa aberta para Ref {venda.fatura_ref}"
        ))
        db.session.commit()
        flash("Disputa aberta. O suporte entrará em contacto.", "warning")

    return redirect(url_for('comprador.dashboard'))

@comprador_bp.route('/compra/<int:trans_id>')
@login_required
def detalhes_compra(trans_id): # <-- Este nome tem de ser exatamente igual ao do url_for
    compra = Transacao.query.get_or_404(trans_id)
    return render_template('comprador/detalhes_compra.html', compra=compra)