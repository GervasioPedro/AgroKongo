from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Usuario, Transacao, TransactionStatus
from app.utils.decorators import role_required
from sqlalchemy import func, case
from app.extensions import db

dashboard_api_bp = Blueprint('dashboard_api', __name__)

@dashboard_api_bp.route('/produtor', methods=['GET'])
@jwt_required()
@role_required('produtor')
def get_produtor_dashboard():
    """
    Fornece todos os dados necessários para o painel do produtor.
    """
    user_id = get_jwt_identity()
    
    # KPIs Financeiros
    stats = db.session.query(
        func.sum(case((Transacao.status == TransactionStatus.FINALIZADO, Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status.in_([TransactionStatus.ESCROW, TransactionStatus.ENVIADO]), Transacao.valor_liquido_vendedor), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.ENTREGUE, Transacao.valor_liquido_vendedor), else_=0))
    ).filter(Transacao.vendedor_id == user_id).first()

    # Listas de Vendas
    query = Transacao.query.filter_by(vendedor_id=user_id)
    reservas = query.filter_by(status=TransactionStatus.PENDENTE).order_by(Transacao.data_criacao.desc()).all()
    vendas_ativas = query.filter(Transacao.status.in_([
        TransactionStatus.AGUARDANDO_PAGAMENTO, TransactionStatus.ANALISE,
        TransactionStatus.ESCROW, TransactionStatus.ENVIADO
    ])).order_by(Transacao.data_criacao.desc()).all()
    historico = query.filter(Transacao.status.in_([
        TransactionStatus.ENTREGUE, TransactionStatus.FINALIZADO, TransactionStatus.CANCELADO
    ])).order_by(Transacao.data_criacao.desc()).all()

    user = Usuario.query.get(user_id)

    return jsonify({
        "success": True,
        "data": {
            "kpis": {
                "receita_total": float(stats[0] or 0),
                "receita_pendente": float(stats[1] or 0),
                "receita_a_liquidar": float(stats[2] or 0),
                "saldo_disponivel": float(user.saldo_disponivel or 0)
            },
            "listas": {
                "reservas": [v.to_dict() for v in reservas],
                "vendas_ativas": [v.to_dict() for v in vendas_ativas],
                "historico": [v.to_dict() for v in historico]
            }
        }
    })

@dashboard_api_bp.route('/comprador', methods=['GET'])
@jwt_required()
def get_comprador_dashboard():
    """
    Fornece todos os dados necessários para o painel do comprador.
    """
    user_id = get_jwt_identity()

    query = Transacao.query.filter_by(comprador_id=user_id)

    # Listas
    pendentes = query.filter(Transacao.status.in_([TransactionStatus.PENDENTE, TransactionStatus.AGUARDANDO_PAGAMENTO])).all()
    em_transito = query.filter(Transacao.status.in_([TransactionStatus.ANALISE, TransactionStatus.ESCROW, TransactionStatus.ENVIADO])).all()
    historico = query.filter(Transacao.status.in_([TransactionStatus.ENTREGUE, TransactionStatus.FINALIZADO, TransactionStatus.CANCELADO])).all()

    # KPIs
    total_gasto = db.session.query(func.sum(Transacao.valor_total_pago)).filter(
        Transacao.comprador_id == user_id,
        Transacao.status.in_([TransactionStatus.ENTREGUE, TransactionStatus.FINALIZADO])
    ).scalar() or 0
    compras_ativas = query.filter(Transacao.status.in_([
        TransactionStatus.PENDENTE, TransactionStatus.AGUARDANDO_PAGAMENTO,
        TransactionStatus.ANALISE, TransactionStatus.ESCROW, TransactionStatus.ENVIADO
    ])).count()

    return jsonify({
        "success": True,
        "data": {
            "kpis": {
                "total_gasto": float(total_gasto),
                "compras_ativas": compras_ativas
            },
            "listas": {
                "pendentes": [p.to_dict() for p in pendentes],
                "em_transito": [t.to_dict() for t in em_transito],
                "historico": [h.to_dict() for h in historico]
            }
        }
    })

@dashboard_api_bp.route('/admin', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_admin_dashboard():
    """
    Fornece todos os dados necessários para o painel do admin.
    """
    # KPIs
    financas = db.session.query(
        func.sum(case((Transacao.status != TransactionStatus.CANCELADO, Transacao.valor_total_pago), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.FINALIZADO, Transacao.comissao_plataforma), else_=0)),
        func.sum(case((Transacao.status == TransactionStatus.ENTREGUE, Transacao.valor_liquido_vendedor), else_=0))
    ).first()
    total_utilizadores = Usuario.query.count()

    # Listas de Tarefas
    pendentes_validacao = Transacao.query.filter_by(status=TransactionStatus.ANALISE).order_by(Transacao.data_criacao.asc()).all()
    aguardando_liquidacao = Transacao.query.filter_by(status=TransactionStatus.ENTREGUE, transferencia_concluida=False).all()

    return jsonify({
        "success": True,
        "data": {
            "kpis": {
                "total_vendas": float(financas[0] or 0),
                "comissao_total": float(financas[1] or 0),
                "divida_produtores": float(financas[2] or 0),
                "total_utilizadores": total_utilizadores
            },
            "tarefas": {
                "validar_pagamentos": [p.to_dict() for p in pendentes_validacao],
                "liquidar_pagamentos": [l.to_dict() for l in aguardando_liquidacao]
            }
        }
    })