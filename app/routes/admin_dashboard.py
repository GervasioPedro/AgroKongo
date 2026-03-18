"""
Blueprint para operações de dashboard e KPIs do Admin.
Responsável apenas por métricas e visão geral.
"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, case

from app.extensions import db
from app.models import (
    Usuario, Transacao, Safra, Produto, 
    TransactionStatus, LogAuditoria
)
from app.utils.status_helper import status_to_value
from functools import wraps

admin_dashboard_bp = Blueprint('admin_dashboard', __name__)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo != 'admin':
            flash("Acesso restrito a administradores.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_dashboard_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Painel de Gestão Centralizada e KPIs Financeiros."""
    # 1. Agregações SQL de Alta Performance
    financas = db.session.query(
        func.sum(case((Transacao.status != status_to_value(TransactionStatus.CANCELADO), Transacao.valor_total_pago), else_=0)),
        func.sum(case((Transacao.status == status_to_value(TransactionStatus.FINALIZADO), Transacao.comissao_plataforma), else_=0)),
        func.sum(case((Transacao.status == status_to_value(TransactionStatus.ENTREGUE), Transacao.valor_liquido_vendedor), else_=0))
    ).first()

    # 2. Filas de Trabalho Prioritárias
    pendentes_validacao = Transacao.query.filter_by(status=status_to_value(TransactionStatus.ANALISE)) \
        .order_by(Transacao.data_criacao.asc()).all()

    aguardando_liquidacao = Transacao.query.filter_by(
        status=status_to_value(TransactionStatus.ENTREGUE),
        transferencia_concluida=False
    ).all()

    # 3. Stock Estratégico
    stock_global = db.session.query(Produto.nome, func.sum(Safra.quantidade_disponivel)) \
        .join(Safra).filter(Safra.status == 'disponivel') \
        .group_by(Produto.nome).all()

    return render_template('admin/dashboard.html',
                           total_vendas=financas[0] or 0,
                           comissao_total=financas[1] or 0,
                           divida_produtores=financas[2] or 0,
                           pendentes=pendentes_validacao,
                           dividas=aguardando_liquidacao,
                           safras_ativas=stock_global,
                           total_utilizadores=Usuario.query.count())
