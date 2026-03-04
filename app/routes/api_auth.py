from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.extensions import csrf

api_auth_bp = Blueprint('api_auth', __name__, url_prefix='/api/auth')
csrf.exempt(api_auth_bp)


@api_auth_bp.route('/me', methods=['GET'])
def me():
    """Retorna dados do usuário autenticado"""
    if current_user.is_authenticated:
        return jsonify({
            'autenticado': True,
            'usuario': {
                'id': current_user.id,
                'nome': current_user.nome,
                'telemovel': current_user.telemovel,
                'tipo': current_user.tipo,
                'email': current_user.email
            }
        })
    return jsonify({'autenticado': False}), 401
