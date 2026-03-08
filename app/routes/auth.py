from flask import Blueprint, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, login_manager, csrf, limiter
from app.models import Usuario, LogAuditoria
from app.shared.constants import (
    SEGURANCA_MAX_LOGIN_TENTATIVAS,
    SEGURANCA_LOCKOUT_MINUTOS,
    AUDITORIA_ACOES
)
from app.shared.responses import success_response, error_response, validation_error, unauthorized_error

import re


auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def _autenticar_usuario(telemovel, senha):
    usuario = Usuario.query.filter_by(telemovel=telemovel).first()
    if usuario and usuario.verificar_senha(senha):
        return usuario
    return None


def _registrar_login(usuario_id, detalhes):
    db.session.add(LogAuditoria(
        usuario_id=usuario_id,
        acao=AUDITORIA_ACOES['LOGIN'],
        detalhes=detalhes
    ))
    db.session.commit()


@auth_bp.route('/api/auth/login', methods=['POST'])
@csrf.exempt
@limiter.limit(f"{SEGURANCA_MAX_LOGIN_TENTATIVAS} per {SEGURANCA_LOCKOUT_MINUTOS} minute")
def api_login():
    if current_user.is_authenticated:
        return success_response(
            data=current_user.to_dict(),
            message='Login realizado com sucesso'
        )

    payload = request.get_json(silent=True) or {}
    telemovel = re.sub(r'\D', '', payload.get('telemovel', ''))
    senha = payload.get('senha')

    if not telemovel or not senha:
        return error_response(
            message='Preencha o telemóvel e a senha.',
            status_code=400
        )

    usuario = _autenticar_usuario(telemovel, senha)

    if usuario:
        login_user(usuario, remember=True)
        _registrar_login(usuario.id, f"Acesso via {request.remote_addr} (API)")
        return success_response(
            data=usuario.to_dict(),
            message='Login realizado com sucesso'
        )

    return error_response(
        message='Credenciais inválidas.',
        status_code=401
    )


@auth_bp.route('/api/auth/me')
def api_me():
    if not current_user.is_authenticated:
        return unauthorized_error(message='Não autenticado')
    return success_response(
        data=current_user.to_dict(),
        message='Usuário autenticado'
    )


@auth_bp.route('/api/auth/logout', methods=['POST'])
@csrf.exempt
@login_required
def api_logout():
    if not current_user.is_authenticated:
        return unauthorized_error(message='Não autenticado')

    db.session.add(LogAuditoria(
        usuario_id=current_user.id,
        acao=AUDITORIA_ACOES['LOGOUT']
    ))
    db.session.commit()
    logout_user()
    return success_response(message='Logout realizado com sucesso')


@auth_bp.route('/api/profile', methods=['PUT'])
@login_required
def api_update_profile():
    """Atualiza os dados do perfil do utilizador autenticado."""
    data = request.form
    user = current_user

    try:
        if 'nome' in data:
            user.nome = data['nome'].strip().title()

        if 'email' in data and data['email'] != user.email:
            if Usuario.query.filter(Usuario.email == data['email'], Usuario.id != user.id).first():
                return error_response(
                    message='Este e-mail já está em uso.',
                    status_code=409
                )
            user.email = data['email'].strip().lower()

        if 'nif' in data:
            user.nif = data['nif']
        if 'provincia_id' in data:
            user.provincia_id = int(data['provincia_id'])
        if 'municipio_id' in data:
            user.municipio_id = int(data['municipio_id'])

        if user.tipo == 'produtor' and 'iban' in data:
            user.iban = data['iban'].replace(' ', '').upper()

        user.verificar_e_atualizar_perfil()
        db.session.commit()

        return success_response(
            data=user.to_dict(),
            message='Perfil atualizado com sucesso!'
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API_UPDATE_PROFILE: {str(e)}")
        return error_response(
            message='Ocorreu um erro ao atualizar o perfil.',
            status_code=500
        )


@auth_bp.route('/api/profile/change-password', methods=['PUT'])
@login_required
def api_change_password():
    """Altera a palavra-passe do utilizador autenticado."""
    payload = request.get_json(silent=True) or {}
    senha_atual = payload.get('senha_atual')
    nova_senha = payload.get('nova_senha')

    if not senha_atual or not nova_senha:
        return error_response(
            message='Todos os campos são obrigatórios.',
            status_code=400
        )

    if not current_user.verificar_senha(senha_atual):
        return error_response(
            message='A palavra-passe atual está incorreta.',
            status_code=403
        )

    if not (nova_senha and len(nova_senha) >= 6):
        return validation_error(
            field='nova_senha',
            message='A nova palavra-passe deve ter no mínimo 6 caracteres.'
        )

    try:
        current_user.set_senha(nova_senha)
        db.session.commit()
        return success_response(message='Palavra-passe atualizada com sucesso!')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API_CHANGE_PASSWORD: {e}")
        return error_response(
            message='Erro ao atualizar a palavra-passe.',
            status_code=500
        )
