from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf.csrf import validate_csrf
from wtforms import ValidationError

from app.extensions import db, login_manager, csrf, limiter
from app.models import Usuario, LogAuditoria

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
        acao="LOGIN_SUCCESS",
        detalhes=detalhes
    ))
    db.session.commit()


@auth_bp.route('/api/auth/login', methods=['POST'])
@csrf.exempt
@limiter.limit("5 per minute")
def api_login():
    if current_user.is_authenticated:
        return jsonify({'ok': True, 'user': current_user.to_dict()})

    payload = request.get_json(silent=True) or {}
    telemovel = re.sub(r'\D', '', payload.get('telemovel', ''))
    senha = payload.get('senha')

    if not telemovel or not senha:
        return jsonify({'ok': False, 'message': 'Preencha o telemovel e a senha.'}), 400

    usuario = _autenticar_usuario(telemovel, senha)

    if usuario:
        login_user(usuario, remember=True)
        _registrar_login(usuario.id, f"Acesso via {request.remote_addr} (API)")
        return jsonify({'ok': True, 'user': usuario.to_dict()})

    return jsonify({'ok': False, 'message': 'Credenciais invalidas.'}), 401


@auth_bp.route('/api/auth/me')
def api_me():
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'message': 'Nao autenticado.'}), 401
    return jsonify({'ok': True, 'user': current_user.to_dict()})


@auth_bp.route('/api/auth/logout', methods=['POST'])
@csrf.exempt
@login_required
def api_logout():
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'message': 'Não autenticado.'}), 401

    db.session.add(LogAuditoria(usuario_id=current_user.id, acao="LOGOUT"))
    db.session.commit()
    logout_user()
    return jsonify({'ok': True})


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
                return jsonify({'ok': False, 'message': 'Este e-mail já está em uso.'}), 409
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

        return jsonify({'ok': True, 'user': user.to_dict(), 'message': 'Perfil atualizado com sucesso!'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API_UPDATE_PROFILE: {str(e)}")
        return jsonify({'ok': False, 'message': 'Ocorreu um erro ao atualizar o perfil.'}), 500


@auth_bp.route('/api/profile/change-password', methods=['PUT'])
@login_required
def api_change_password():
    """Altera a palavra-passe do utilizador autenticado."""
    payload = request.get_json(silent=True) or {}
    senha_atual = payload.get('senha_atual')
    nova_senha = payload.get('nova_senha')

    if not senha_atual or not nova_senha:
        return jsonify({'ok': False, 'message': 'Todos os campos são obrigatórios.'}), 400

    if not current_user.verificar_senha(senha_atual):
        return jsonify({'ok': False, 'message': 'A palavra-passe atual está incorreta.'}), 403

    if not (nova_senha and len(nova_senha) >= 6):
        return jsonify({'ok': False, 'message': 'A nova palavra-passe deve ter no mínimo 6 caracteres.'}), 400

    try:
        current_user.set_senha(nova_senha)
        db.session.commit()
        return jsonify({'ok': True, 'message': 'Palavra-passe atualizada com sucesso!'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO API_CHANGE_PASSWORD: {e}")
        return jsonify({'ok': False, 'message': 'Erro ao atualizar a palavra-passe.'}), 500
