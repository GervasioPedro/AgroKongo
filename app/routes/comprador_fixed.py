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
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import joinedload # Importar joinedload
from markupsafe import escape

from app.extensions import db
from app.models import (
    Transacao, Safra, Usuario, LogAuditoria,
    HistoricoStatus, Notificacao, TransactionStatus
)
from app.utils.helpers import salvar_ficheiro

comprador_bp = Blueprint('comprador', __name__)


@comprador_bp.route('/dashboard')
@login_required
def dashboard():
    base_query = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.vendedor)
    ).filter(Transacao.comprador_id == current_user.id)

    pendentes = base_query.filter(Transacao.status.in_([
        TransactionStatus.PENDENTE,
        TransactionStatus.AGUARDANDO_PAGAMENTO
    ])).all()

    em_transito = base_query.filter(Transacao.status.in_([
        TransactionStatus.ANALISE,
        TransactionStatus.ESCROW,
        TransactionStatus.ENVIADO
    ])).order_by(Transacao.data_envio.desc()).all()

    historico = base_query.filter(Transacao.status.in_([
        TransactionStatus.ENTREGUE,
        TransactionStatus.FINALIZADO,
        TransactionStatus.CANCELADO
    ])).order_by(Transacao.data_entrega.desc()).all()

    total_gasto = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_([TransactionStatus.ENTREGUE, TransactionStatus.FINALIZADO])
    ).scalar() or 0

    compras_ativas = base_query.filter(Transacao.status != TransactionStatus.FINALIZADO).count()

    return render_template('painel/comprador.html',
                           pendentes=pendentes,
                           em_transito=em_transito,
                           historico=historico,
                           total_gasto=total_gasto,
                           compras_ativas=compras_ativas)


@comprador_bp.route('/minhas-reservas')
@login_required
def minhas_reservas():
    transacoes = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.vendedor)
    ).filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_([TransactionStatus.PENDENTE, TransactionStatus.AGUARDANDO_PAGAMENTO])
    ).order_by(Transacao.data_criacao.desc()).all()
    return render_template('comprador/minhas_reservas.html', transacoes=transacoes)


@comprador_bp.route('/pagar-reserva/<int:trans_id>')
@login_required
def pagar_reserva(trans_id):
    venda = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.vendedor)
    ).get_or_404(trans_id)

    if venda.comprador_id != current_user.id:
        abort(403)

    if venda.status == TransactionStatus.PENDENTE:
        flash("Aguarde a confirmacao de stock pelo produtor antes de pagar.", "warning")
        return redirect(url_for('comprador.minhas_reservas'))

    if venda.status != TransactionStatus.AGUARDANDO_PAGAMENTO:
        flash("Esta transacao ja nao se encontra em fase de pagamento.", "info")
        return redirect(url_for('comprador.minhas_compras'))

    return render_template('comprador/pagar_reserva.html', transacao=venda)


@comprador_bp.route('/submeter-comprovativo/<int:trans_id>', methods=['POST'])
@login_required
def submeter_comprovativo(trans_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
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
            observacao="Talao submetido via dashboard do comprador."
        ))

        db.session.commit()
        flash("Talao enviado! O Admin validara o pagamento em breve.", "success")
        return redirect(url_for('comprador.minhas_compras'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro no upload: {e}")
        flash("Erro tecnico ao processar ficheiro.", "danger")
        return redirect(url_for('comprador.pagar_reserva', trans_id=trans_id))


@comprador_bp.route('/minhas-compras')
@login_required
def minhas_compras():
    status_compras = [
        TransactionStatus.ANALISE, TransactionStatus.ESCROW,
        TransactionStatus.ENVIADO, TransactionStatus.ENTREGUE,
        TransactionStatus.FINALIZADO, TransactionStatus.DISPUTA
    ]
    compras = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.vendedor)
    ).filter(
        Transacao.comprador_id == current_user.id,
        Transacao.status.in_(status_compras)
    ).order_by(Transacao.data_criacao.desc()).all()

    return render_template('comprador/minhas_compras.html', compras=compras)


@comprador_bp.route('/confirmar-recebimento/<int:trans_id>', methods=['POST'])
@login_required
def confirmar_recebimento(trans_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)

    transacao = Transacao.query.options(
        joinedload(Transacao.vendedor)
    ).with_for_update().get_or_404(trans_id)

    if transacao.comprador_id != current_user.id:
        abort(403)

    if transacao.status != TransactionStatus.ENVIADO:
        flash("Esta encomenda nao esta em estado de recepcao.", "warning")
        return redirect(url_for('comprador.dashboard'))

    try:
        transacao.status = TransactionStatus.ENTREGUE
        transacao.data_entrega = datetime.now(timezone.utc)

        vendedor = transacao.vendedor

        valor_a_pagar = Decimal(str(transacao.valor_liquido_vendedor))
        vendedor.saldo_disponivel = (vendedor.saldo_disponivel or 0) + valor_a_pagar

        db.session.add(Notificacao(
            usuario_id=vendedor.id,
            mensagem=f"Saldo libertado! Recebeste o pagamento da fatura {escape(transacao.fatura_ref)}.",
            link=url_for('produtor.vendas')
        ))

        db.session.commit()
        flash("Recebimento confirmado! O saldo foi libertado para o produtor.", "success")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_RECEBIMENTO: {e}")
        flash("Erro ao processar a confirmacao.", "danger")

    return redirect(url_for('comprador.dashboard'))

@comprador_bp.route('/avaliar/<int:trans_id>', methods=['POST'])
@login_required
def avaliar_venda(trans_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    venda = Transacao.query.options(
        joinedload(Transacao.vendedor)
    ).get_or_404(trans_id)
    if venda.comprador_id != current_user.id:
        flash("Acao nao permitida.", "danger")
        return redirect(url_for('comprador.minhas_compras'))

    try:
        estrelas = int(request.form.get('estrelas', 5))
        if estrelas < 1 or estrelas > 5:
            estrelas = 5
        
        comentario = escape(request.form.get('comentario', ''))
        
        db.session.add(Notificacao(
            usuario_id=venda.vendedor_id,
            mensagem=f"Recebeste {estrelas} estrelas na venda {escape(venda.fatura_ref)}!"
        ))
        db.session.commit()
        flash("Obrigado pela sua avaliacao!", "success")
    except:
        db.session.rollback()
        flash("Erro ao submeter avaliacao.", "danger")

    return redirect(url_for('comprador.minhas_compras'))


@comprador_bp.route('/abrir-disputa/<int:trans_id>', methods=['POST'])
@login_required
def abrir_disputa(trans_id):
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    venda = Transacao.query.with_for_update().get_or_404(trans_id)
    if venda.comprador_id != current_user.id:
        abort(403)

    if not venda.transferencia_concluida:
        venda.status = TransactionStatus.DISPUTA
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="DISPUTA",
            detalhes=f"Disputa aberta para Ref {escape(venda.fatura_ref)}"
        ))
        db.session.commit()
        flash("Disputa aberta. O suporte entrara em contacto.", "warning")

    return redirect(url_for('comprador.dashboard'))

@comprador_bp.route('/compra/<int:trans_id>')
@login_required
def detalhes_compra(trans_id):
    compra = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.vendedor),
        joinedload(Transacao.comprador)
    ).get_or_404(trans_id)
    
    if compra.comprador_id != current_user.id and current_user.tipo != 'admin':
        abort(403)
    
    return render_template('comprador/detalhes_compra.html', compra=compra)
