# app/routes/comprador.py - Versão consolidada e otimizada
import hashlib
import base64
import qrcode
from io import BytesIO
from datetime import datetime, timezone
from decimal import Decimal

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, abort, make_response, jsonify
)
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError, OperationalError

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
    """
    try:
        transacao = Transacao.query.filter_by(uuid=trans_uuid).with_for_update().first_or_404()
        
        if transacao.comprador_id != current_user.id:
            abort(403)
        
        if transacao.status != TransactionStatus.ENVIADO:
            flash("Esta encomenda não está em estado de receção.", "warning")
            return redirect(url_for('comprador.dashboard'))
        
        transacao.status = TransactionStatus.ENTREGUE
        transacao.data_entrega = datetime.now(timezone.utc)
        
        task = processar_liquidacao.delay(transacao.id)
        
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="CONFIRMACAO_RECEBIMENTO",
            detalhes=f"Usuário confirmou recebimento da transação {transacao.fatura_ref}. Task {task.id} disparada."
        ))
        
        db.session.add(Notificacao(
            usuario_id=transacao.vendedor_id,
            mensagem=f"📦 Recebimento confirmado! {transacao.fatura_ref} em processamento financeiro.",
            link=url_for('produtor.vendas')
        ))
        
        db.session.commit()
        
        flash("✅ Sucesso! Estamos a processar a transferência para o produtor em segundo plano.", "success")
        
    except OperationalError as e:
        db.session.rollback()
        current_app.logger.critical(f"ERRO_RECEBIMENTO_UUID {trans_uuid} - Erro de DB: {e}")
        flash("Erro de comunicação com o servidor. Tente novamente.", "danger")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_RECEBIMENTO_UUID {trans_uuid}: {e}")
        flash("Erro ao processar a confirmação. Tente novamente.", "danger")
    
    return redirect(url_for('comprador.dashboard'))


@comprador_bp.route('/dashboard')
@login_required
def dashboard():
    """Painel do Comprador com métricas reais."""
    # ... (código existente sem alterações)
    base_query = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.vendedor),
        joinedload(Transacao.comprador)
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


@comprador_bp.route('/api/comprador/avaliar-venda/<int:id>', methods=['POST'])
@login_required
def api_avaliar_venda(id):
    """Permite que um comprador avalie uma transação concluída."""
    try:
        venda = Transacao.query.options(
            joinedload(Transacao.vendedor)
        ).filter_by(id=id, comprador_id=current_user.id).first_or_404()
        
        if venda.status not in [TransactionStatus.ENTREGUE, TransactionStatus.FINALIZADO]:
            return jsonify({'ok': False, 'message': 'Só pode avaliar transações concluídas.'}), 409

        payload = request.get_json(silent=True) or {}
        estrelas = payload.get('estrelas')
        comentario = payload.get('comentario', '')

        if not estrelas or not isinstance(estrelas, int) or not 1 <= estrelas <= 5:
            return jsonify({'ok': False, 'message': 'A avaliação em estrelas (1 a 5) é obrigatória.'}), 400

        if Avaliacao.query.filter_by(transacao_id=venda.id).first():
            return jsonify({'ok': False, 'message': 'Esta transação já foi avaliada.'}), 409

        nova_av = Avaliacao(
            transacao_id=venda.id,
            produtor_id=venda.vendedor_id,
            comprador_id=current_user.id,
            estrelas=estrelas,
            comentario=comentario
        )
        db.session.add(nova_av)
        db.session.add(Notificacao(
            usuario_id=venda.vendedor_id,
            mensagem=f"⭐ Recebeste uma nova avaliação de {estrelas} estrelas na venda {venda.fatura_ref}!"
        ))
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Obrigado pela sua avaliação!'})
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API AVALIAR VENDA - Integridade: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao guardar a avaliação.'}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API AVALIAR VENDA: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao submeter avaliação.'}), 500


@comprador_bp.route('/api/comprador/abrir-disputa/<int:id>', methods=['POST'])
@login_required
def api_abrir_disputa(id):
    """Abre uma disputa para uma transação, bloqueando o pagamento."""
    try:
        venda = Transacao.query.with_for_update().get_or_404(id)
        if venda.comprador_id != current_user.id:
            return jsonify({'ok': False, 'message': 'Acesso não permitido.'}), 403

        if venda.status in [TransactionStatus.FINALIZADO, TransactionStatus.CANCELADO]:
            return jsonify({'ok': False, 'message': 'Não é possível abrir disputa para esta transação.'}), 409

        if venda.status == TransactionStatus.DISPUTA:
            return jsonify({'ok': False, 'message': 'Já existe uma disputa aberta.'}), 409

        venda.status = TransactionStatus.DISPUTA
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="DISPUTA_API",
            detalhes=f"Disputa aberta para Ref {venda.fatura_ref}"
        ))
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Disputa aberta. O suporte entrará em contacto.'})
    except OperationalError as e:
        db.session.rollback()
        current_app.logger.critical(f"ERRO API ABRIR DISPUTA - Erro de DB: {e}")
        return jsonify({'ok': False, 'message': 'Erro de comunicação com o servidor.'}), 503
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API ABRIR DISPUTA: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao abrir disputa.'}), 500
