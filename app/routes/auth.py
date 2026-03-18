from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.extensions import db, login_manager, csrf
from app.models import Usuario, LogAuditoria
from app.utils.helpers import salvar_ficheiro
import re
import sys
from werkzeug.security import generate_password_hash

# Blueprint para rotas de template (HTML) - Prefixo /auth
auth_bp = Blueprint('auth', __name__)

# Blueprint para rotas de API (JSON) - Prefixo /api/auth
auth_api_bp = Blueprint('auth_api', __name__) 

# Desativar CSRF para a API
csrf.exempt(auth_api_bp) 


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# ==========================================
# ROTAS DE TEMPLATE (Legado/Admin)
# ==========================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        senha = request.form.get('senha')
        usuario = Usuario.query.filter_by(telemovel=telemovel).first()

        if usuario and usuario.verificar_senha(senha):
            login_user(usuario, remember=True)
            return redirect(url_for('main.dashboard'))

        flash('Credenciais inválidas.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/registo', methods=['GET', 'POST'])
def registo():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    return render_template('auth/registo.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão terminada.', 'info')
    return redirect(url_for('auth.login'))


# ==========================================
# API ENDPOINTS PARA REACT / NEXT.JS
# ==========================================

@auth_api_bp.route('/login', methods=['POST'])
def login_api():
    try:
        data = request.get_json(silent=True)
        if not data: return jsonify({"success": False, "errors": ["JSON inválido"]}), 400
        
        email_tel = data.get('email')
        senha = data.get('senha')

        if not email_tel or not senha:
            return jsonify({"success": False, "errors": ["Email/Telemóvel e senha obrigatórios"]}), 400
        
        usuario = Usuario.query.filter(
            (Usuario.email == email_tel) | 
            (Usuario.telemovel == email_tel)
        ).first()
        
        if not usuario or not usuario.verificar_senha(senha):
            return jsonify({"success": False, "errors": ["Credenciais inválidas"]}), 401
        
        additional_claims = {"role": usuario.tipo, "verified": usuario.conta_validada}
        access_token = create_access_token(identity=str(usuario.id), additional_claims=additional_claims)
        
        return jsonify({
            "success": True,
            "data": {
                "access_token": access_token,
                "user": usuario.to_dict()
            }
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "errors": [str(e)]}), 500


@auth_api_bp.route('/registro', methods=['POST'])
def registro_api():
    try:
        data = request.get_json(silent=True)
        if not data: return jsonify({"success": False, "errors": ["Payload JSON vazio"]}), 400

        nome = data.get('nome', '').strip()
        email = data.get('email', '').strip().lower() if data.get('email') else None
        senha = data.get('senha')
        tipo = data.get('tipo', 'comprador')
        
        telemovel_raw = str(data.get('telemovel', ''))
        telemovel = re.sub(r'\D', '', telemovel_raw)
        if not telemovel: telemovel = None

        if not nome or not senha:
             return jsonify({"success": False, "errors": ["Nome e Senha são obrigatórios"]}), 400
             
        if not email and not telemovel:
             return jsonify({"success": False, "errors": ["Indique Email ou Telemóvel"]}), 400

        if email and Usuario.query.filter_by(email=email).first():
            return jsonify({"success": False, "errors": [f'Email {email} já registado.']}), 409
            
        if telemovel and Usuario.query.filter_by(telemovel=telemovel).first():
            return jsonify({"success": False, "errors": [f'Telemóvel {telemovel} já registado.']}), 409
            
        usuario = Usuario(
            nome=nome,
            email=email,
            telemovel=telemovel,
            tipo=tipo,
            perfil_completo=False,
            conta_validada=False
        )
        usuario.senha = senha
        
        db.session.add(usuario)
        db.session.commit()
        
        access_token = create_access_token(identity=str(usuario.id), additional_claims={"role": tipo})
        
        return jsonify({
            "success": True,
            "data": {
                "access_token": access_token,
                "user": usuario.to_dict(),
                "next_step": "/completar-perfil"
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "errors": [f'Erro interno: {str(e)}']}), 500


@auth_api_bp.route('/completar-perfil', methods=['POST'])
@jwt_required()
def completar_perfil_api():
    """
    Endpoint multipart/form-data para completar perfil com foto.
    """
    try:
        current_user_id = get_jwt_identity()
        usuario = Usuario.query.get(int(current_user_id))
        
        if not usuario:
            return jsonify({"success": False, "errors": ["Utilizador não encontrado"]}), 404

        # Dados do Form
        nif = request.form.get('nif')
        iban = request.form.get('iban')
        provincia_id = request.form.get('provincia_id')
        municipio_id = request.form.get('municipio_id')
        foto = request.files.get('foto_perfil')

        # Validações
        if not nif or not provincia_id or not municipio_id:
             return jsonify({"success": False, "errors": ["NIF e Localização são obrigatórios"]}), 400

        # Atualização
        usuario.nif = nif
        usuario.iban = iban
        usuario.provincia_id = int(provincia_id)
        usuario.municipio_id = int(municipio_id)
        
        if foto:
            nome_foto = salvar_ficheiro(foto, subpasta='perfil')
            if nome_foto:
                usuario.foto_perfil = nome_foto

        usuario.perfil_completo = True
        
        # Se for produtor, precisa de validação extra do admin
        if usuario.tipo == 'produtor':
            usuario.conta_validada = False 
        else:
            usuario.conta_validada = True # Compradores validam automaticamente (MVP)

        db.session.commit()
        
        return jsonify({
            "success": True,
            "data": {
                "next_step": '/dashboard',
                "user": usuario.to_dict()
            }
        }), 200
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "errors": [str(e)]}), 500
