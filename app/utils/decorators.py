from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models import Usuario

def role_required(roles):
    """
    Decorador para proteger rotas com base no tipo de utilizador (RBAC).
    Aceita uma string ('admin') ou uma lista (['produtor', 'admin']).
    """
    if isinstance(roles, str):
        roles = [roles]

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # 1. Garante que o JWT é válido
            verify_jwt_in_request()

            # 2. Obtém o ID do utilizador do token
            user_id = get_jwt_identity()
            user = Usuario.query.get(user_id)

            if not user:
                return jsonify({'error': 'Utilizador não encontrado'}), 404

            # 3. Verifica se o tipo do utilizador está na lista permitida
            if user.tipo not in roles:
                return jsonify({'error': 'Acesso proibido: Permissão insuficiente'}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper

def kyc_required():
    """
    Decorador para garantir que a conta foi validada pelo Admin (KYC).
    Essencial para operações financeiras (criar safra, comprar).
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = Usuario.query.get(user_id)

            if not user:
                return jsonify({'error': 'Utilizador não encontrado'}), 404

            if not user.conta_validada:
                return jsonify({'error': 'A sua conta ainda não foi validada pela administração.'}), 403

            return fn(*args, **kwargs)
        return decorator
    return wrapper