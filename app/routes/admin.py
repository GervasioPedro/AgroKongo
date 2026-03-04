from flask import Blueprint, request, current_app, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, or_, case
from app.models import Usuario, Transacao, Notificacao, LogAuditoria, TransactionStatus
from app.extensions import db
from app.utils.decorators import admin_required
from decimal import Decimal
from datetime import datetime, timezone

admin_bp = Blueprint('admin', __name__)

# ==================== API ENDPOINTS (JSON) ====================

@admin_bp.route('/api/admin/dashboard-stats', methods=['GET'])
@login_required
@admin_required
def api_dashboard_stats():
    # ... (código da API)
    pass

@admin_bp.route('/api/admin/transacoes', methods=['GET'])
@login_required
@admin_required
def api_get_transacoes():
    # ... (código da API)
    pass

@admin_bp.route('/api/admin/usuarios', methods=['GET'])
@login_required
@admin_required
def api_get_usuarios():
    users = Usuario.query.order_by(Usuario.id.desc()).limit(500).all()
    def to_json(u: Usuario):
        return {
            'id': u.id,
            'nome': u.nome,
            'email': getattr(u, 'email', '') or f"{u.telemovel}@agrokongo",
            'tipo': getattr(u, 'tipo', None),
            'conta_validada': bool(getattr(u, 'conta_validada', False)),
            'provincia': getattr(getattr(u, 'provincia', None), 'nome', None)
        }
    return jsonify({'usuarios': [to_json(u) for u in users]})

@admin_bp.route('/api/admin/validar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def api_validar_pagamento(id):
    # ... (código da API)
    pass

@admin_bp.route('/api/admin/rejeitar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def api_rejeitar_pagamento(id):
    # ... (código da API)
    pass

@admin_bp.route('/api/admin/confirmar-transferencia/<int:id>', methods=['POST'])
@login_required
@admin_required
def api_confirmar_transferencia(id):
    # ... (código da API)
    pass

@admin_bp.route('/api/admin/resolver-disputa/<int:id>', methods=['POST'])
@login_required
@admin_required
def api_resolver_disputa(id):
    # ... (código da API)
    pass

@admin_bp.route('/api/admin/validar-usuario/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def api_validar_usuario(user_id):
    u = Usuario.query.get_or_404(user_id)
    u.conta_validada = True
    db.session.add(LogAuditoria(usuario_id=current_user.id, acao='ADMIN_VALIDOU_USUARIO', detalhes=f'user_id={u.id}'))
    db.session.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/admin/bloquear-usuario/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def api_bloquear_usuario(user_id):
    u = Usuario.query.get_or_404(user_id)
    u.conta_validada = False
    db.session.add(LogAuditoria(usuario_id=current_user.id, acao='ADMIN_BLOQUEOU_USUARIO', detalhes=f'user_id={u.id}'))
    db.session.commit()
    return jsonify({'ok': True})

@admin_bp.route('/api/admin/usuario/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def api_eliminar_usuario(user_id):
    # ... (código da API)
    pass
