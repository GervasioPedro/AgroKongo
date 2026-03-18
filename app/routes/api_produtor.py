from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_subject
from sqlalchemy import func, case
from app.models import Transacao, TransactionStatus, Usuario
from app.utils.decorators import role_required

api_produtor_bp = Blueprint('api_produtor', __name__)

@api_produtor_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required('produtor')
def get_produtor_dashboard():
    """
    Endpoint para o dashboard do produtor.
    Retorna KPIs financeiros e listas de transações (reservas, ativas, histórico).
    """
    try:
        current_user_id = get_jwt_identity()
        produtor = Usuario.query.get(current_user_id)

        if not produtor:
            return jsonify({"success": False, "errors": ["Produtor não encontrado"]}), 404

        # 1. KPIs Financeiros
        stats = db.session.query(
            func.sum(case((Transacao.status == TransactionStatus.FINALIZADO, Transacao.valor_liquido_vendedor), else_=0)),
            func.sum(case((Transacao.status.in_([TransactionStatus.ESCROW, TransactionStatus.ENVIADO]), Transacao.valor_liquido_vendedor), else_=0)),
            func.sum(case((Transacao.status == TransactionStatus.ENTREGUE, Transacao.valor_liquido_vendedor), else_=0))
        ).filter(Transacao.vendedor_id == current_user_id).first()

        receita_total = float(stats[0] or 0.0)
        receita_pendente = float(stats[1] or 0.0)
        receita_a_liquidar = float(stats[2] or 0.0)
        saldo_disponivel = float(produtor.saldo_disponivel or 0.0)

        # 2. Listas de Transações
        query = Transacao.query.filter_by(vendedor_id=current_user_id)

        reservas = query.filter_by(status=TransactionStatus.PENDENTE).order_by(Transacao.data_criacao.desc()).all()
        vendas_ativas = query.filter(Transacao.status.in_([
            TransactionStatus.AGUARDANDO_PAGAMENTO,
            TransactionStatus.ANALISE,
            TransactionStatus.ESCROW,
            TransactionStatus.ENVIADO
        ])).order_by(Transacao.data_criacao.desc()).all()
        historico = query.filter(Transacao.status.in_([
            TransactionStatus.ENTREGUE,
            TransactionStatus.FINALIZADO,
            TransactionStatus.CANCELADO,
            TransactionStatus.DISPUTA
        ])).order_by(Transacao.data_criacao.desc()).all()

        return jsonify({
            "success": True,
            "data": {
                "kpis": {
                    "receita_total": receita_total,
                    "receita_pendente": receita_pendente,
                    "receita_a_liquidar": receita_a_liquidar,
                    "saldo_disponivel": saldo_disponivel,
                },
                "transacoes": {
                    "reservas": [t.to_dict() for t in reservas],
                    "vendas_ativas": [t.to_dict() for t in vendas_ativas],
                    "historico": [t.to_dict() for t in historico],
                }
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500
