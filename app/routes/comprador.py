# ... (imports e código existente) ...
from flask import Blueprint, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models import Transacao, Notificacao, Avaliacao, LogAuditoria, TransactionStatus
from app.extensions import db
# ...

comprador_bp = Blueprint('comprador', __name__)

# ==================== API ENDPOINTS (JSON) ====================

# ... (api_dashboard_comprador, api_minhas_compras, api_detalhes_compra, etc.) ...

@comprador_bp.route('/api/comprador/avaliar-venda/<int:id>', methods=['POST'])
@login_required
def api_avaliar_venda(id):
    """Permite que um comprador avalie uma transação concluída."""
    venda = Transacao.query.filter_by(id=id, comprador_id=current_user.id).first_or_404()
    
    if venda.status not in [TransactionStatus.ENTREGUE, TransactionStatus.FINALIZADO]:
        return jsonify({'ok': False, 'message': 'Só pode avaliar transações concluídas.'}), 409

    payload = request.get_json(silent=True) or {}
    estrelas = payload.get('estrelas')
    comentario = payload.get('comentario', '')

    if not estrelas or not isinstance(estrelas, int) or not 1 <= estrelas <= 5:
        return jsonify({'ok': False, 'message': 'A avaliação em estrelas (1 a 5) é obrigatória.'}), 400

    try:
        # Evitar avaliações duplicadas
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
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API AVALIAR VENDA: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao submeter avaliação.'}), 500

@comprador_bp.route('/api/comprador/abrir-disputa/<int:id>', methods=['POST'])
@login_required
def api_abrir_disputa(id):
    """Abre uma disputa para uma transação, bloqueando o pagamento."""
    venda = Transacao.query.with_for_update().get_or_404(id)
    if venda.comprador_id != current_user.id:
        return jsonify({'ok': False, 'message': 'Acesso não permitido.'}), 403

    # Regra de negócio: só se pode abrir disputa antes da libertação do pagamento
    if venda.status in [TransactionStatus.FINALIZADO, TransactionStatus.CANCELADO]:
        return jsonify({'ok': False, 'message': 'Não é possível abrir disputa para esta transação.'}), 409

    if venda.status == TransactionStatus.DISPUTA:
        return jsonify({'ok': False, 'message': 'Já existe uma disputa aberta.'}), 409

    try:
        venda.status = TransactionStatus.DISPUTA
        db.session.add(LogAuditoria(
            usuario_id=current_user.id,
            acao="DISPUTA_API",
            detalhes=f"Disputa aberta para Ref {venda.fatura_ref}"
        ))
        # Notificar Admin
        # (Lógica de notificação para admin pode ser adicionada aqui)
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Disputa aberta. O suporte entrará em contacto.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API ABRIR DISPUTA: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao abrir disputa.'}), 500

# ... (resto das rotas) ...
