from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, login_manager, csrf, limiter
from app.models import Usuario, LogAuditoria
from PIL import Image
import secrets
import re
import os

auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def _autenticar_usuario(telemovel, senha):
    """Autentica usuário e retorna instância ou None.
    
    IMPORTANTE: Esta função deve ser chamada apenas de endpoints com proteção CSRF.
    """
    usuario = Usuario.query.filter_by(telemovel=telemovel).first()
    if usuario and usuario.verificar_senha(senha):
        return usuario
    return None


def _registrar_login(usuario_id, detalhes):
    """Registra log de auditoria de login."""
    db.session.add(LogAuditoria(
        usuario_id=usuario_id,
        acao="LOGIN_SUCCESS",
        detalhes=detalhes
    ))
    db.session.commit()


# --- LOGIN COM PROTEÇÃO ---
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            from flask import abort
            abort(403)
        
        # Limpeza de input para evitar espaços acidentais
        telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        senha = request.form.get('senha')

        usuario = _autenticar_usuario(telemovel, senha)

        if usuario:
            login_user(usuario, remember=True)
            _registrar_login(usuario.id, f"Acesso via {request.remote_addr}")
            flash(f'Bem-vindo ao AgroKongo, {usuario.nome.split()[0]}!', 'success')
            return redirect(url_for('main.dashboard'))

        # Mensagem genérica para evitar enumeração de contas
        flash('Credenciais inválidas. Verifique os dados e tente novamente.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/api/auth/login', methods=['POST'])
@csrf.exempt
@limiter.limit("5 per minute")
def api_login():
    if current_user.is_authenticated:
        return jsonify({
            'ok': True,
            'user': current_user.to_dict()
        })

    payload = request.get_json(silent=True) or {}
    telemovel = re.sub(r'\D', '', payload.get('telemovel', ''))
    senha = payload.get('senha')

    if not telemovel or not senha:
        return jsonify({
            'ok': False,
            'message': 'Preencha o telemovel e a senha.'
        }), 400

    usuario = _autenticar_usuario(telemovel, senha)

    if usuario:
        login_user(usuario, remember=True)
        _registrar_login(usuario.id, f"Acesso via {request.remote_addr} (API)")
        return jsonify({
            'ok': True,
            'user': usuario.to_dict()
        })

    return jsonify({
        'ok': False,
        'message': 'Credenciais invalidas. Verifique os dados e tente novamente.'
    }), 401


@auth_bp.route('/api/auth/me')
def api_me():
    if not current_user.is_authenticated:
        return jsonify({
            'ok': False,
            'message': 'Nao autenticado.'
        }), 401
    return jsonify({
        'ok': True,
        'user': current_user.to_dict()
    })


@auth_bp.route('/api/auth/logout', methods=['POST'])
@csrf.exempt
@login_required
def api_logout():
    # Verificação de autorização: usuário deve estar autenticado
    if not current_user.is_authenticated:
        return jsonify({
            'ok': False,
            'message': 'Não autenticado.'
        }), 401
    
    db.session.add(LogAuditoria(usuario_id=current_user.id, acao="LOGOUT"))
    db.session.commit()
    logout_user()
    return jsonify({
        'ok': True
    })


def _validar_telemovel_angolano(telemovel):
    """Valida formato de telemóvel angolano (9 dígitos, começa com 9)."""
    return telemovel.startswith('9') and len(telemovel) == 9


def _validar_senha_minima(senha):
    """Valida senha mínima (6 caracteres)."""
    return len(senha) >= 6


def _criar_usuario(nome, telemovel, tipo, senha):
    """Cria novo usuário no banco de dados."""
    novo_usuario = Usuario(
        nome=nome,
        telemovel=telemovel,
        tipo=tipo,
        perfil_completo=False,
        conta_validada=False
    )
    novo_usuario.set_senha(senha)
    return novo_usuario


# --- REGISTO COM VALIDAÇÃO ANGOLANA ---
@auth_bp.route('/registo', methods=['GET', 'POST'])
def registo():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            from flask import abort
            abort(403)
        
        # Verificação de autorização: apenas tipos permitidos podem ser criados
        tipo = request.form.get('tipo')
        if tipo not in ['produtor', 'comprador']:
            flash('Tipo de conta inválido.', 'danger')
            from flask import abort
            abort(403)
        
        nome = request.form.get('nome', '').strip().title()
        telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        senha = request.form.get('senha')

        # 1. Validação Estrita de Telemóvel
        if not _validar_telemovel_angolano(telemovel):
            flash('Insira um número de telemóvel válido (9 dígitos).', 'warning')
            return redirect(url_for('auth.registo'))

        if Usuario.query.filter_by(telemovel=telemovel).first():
            flash('Este número já está registado. Tente recuperar a senha.', 'info')
            return redirect(url_for('auth.login'))

        # 2. Validação de Senha
        if not _validar_senha_minima(senha):
            flash('A senha deve ter no mínimo 6 caracteres.', 'warning')
            return redirect(url_for('auth.registo'))

        try:
            novo_usuario = _criar_usuario(nome, telemovel, tipo, senha)
            db.session.add(novo_usuario)
            db.session.commit()

            login_user(novo_usuario)
            flash('Conta criada! Complete o perfil para começar a negociar.', 'success')
            return redirect(url_for('main.completar_perfil'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro no registo: {str(e)}")
            flash('Erro técnico ao criar conta. Contacte o suporte.', 'danger')

    return render_template('auth/registo.html')


# --- LOGOUT ---
@auth_bp.route('/logout')
@login_required
def logout():
    db.session.add(LogAuditoria(usuario_id=current_user.id, acao="LOGOUT"))
    db.session.commit()
    logout_user()
    flash('Sessão terminada com segurança.', 'info')
    return redirect(url_for('auth.login'))

def _processar_foto_perfil(arquivo, pasta_perfis):
    """Processa upload de foto de perfil e retorna nome do arquivo."""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(arquivo.filename)
    nome_arquivo = random_hex + f_ext
    caminho_completo = os.path.join(pasta_perfis, nome_arquivo)
    
    try:
        img = Image.open(arquivo)
        img.thumbnail((300, 300))
        img.save(caminho_completo)
    finally:
        if 'img' in locals():
            img.close()
    
    return nome_arquivo


def _remover_foto_antiga(foto_antiga, pasta_perfis):
    """Remove foto de perfil antiga com proteção contra path traversal."""
    if not foto_antiga or foto_antiga == 'default_user.jpg':
        return
    
    # Proteção contra path traversal: apenas basename
    safe_filename = os.path.basename(foto_antiga)
    
    # Validar que não há caracteres perigosos
    if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
        return
    
    pasta_perfis_abs = os.path.abspath(pasta_perfis)
    caminho_antigo = os.path.join(pasta_perfis_abs, safe_filename)
    caminho_antigo_abs = os.path.abspath(caminho_antigo)
    
    # Verificar que o caminho final está dentro da pasta permitida
    if not caminho_antigo_abs.startswith(pasta_perfis_abs + os.sep):
        return
    
    if os.path.exists(caminho_antigo_abs):
        os.remove(caminho_antigo_abs)


# --- EDITAR PERFIL (DENTRO DO PAINEL) ---
@auth_bp.route('/editar_perfil', methods=['POST'])
@login_required
def editar_perfil():
    try:
        # 1. Processamento da Foto de Perfil
        if 'foto_perfil' in request.files:
            arquivo = request.files['foto_perfil']
            if arquivo and arquivo.filename != '':
                pasta_perfis = os.path.join(current_app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil')
                os.makedirs(pasta_perfis, exist_ok=True)
                
                _remover_foto_antiga(current_user.foto_perfil, pasta_perfis)
                current_user.foto_perfil = _processar_foto_perfil(arquivo, pasta_perfis)

        # 2. Dados de Identidade (NOME E NIF BLOQUEADOS)
        # Ignoramos qualquer tentativa de envio via request.form['nome'] ou ['nif']

        # 3. Validação de Telemóvel (Padrão Unitel/Movicel/Africell)
        novo_telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        if novo_telemovel:
            if not novo_telemovel.startswith('9') or len(novo_telemovel) != 9:
                flash('Número inválido. Use o formato de 9 dígitos (ex: 923...).', 'warning')
                return redirect(url_for('main.perfil'))

            # Verificar unicidade
            user_existente = Usuario.query.filter(Usuario.telemovel == novo_telemovel,
                                                  Usuario.id != current_user.id).first()
            if user_existente:
                flash('Este telemóvel já está em uso por outra conta.', 'danger')
                return redirect(url_for('main.perfil'))

            current_user.telemovel = novo_telemovel

        # 4. Validação de Email
        novo_email = request.form.get('email', '').strip().lower()
        if novo_email:
            email_existente = Usuario.query.filter(Usuario.email == novo_email, Usuario.id != current_user.id).first()
            if email_existente:
                flash('Este e-mail já está registado.', 'danger')
                return redirect(url_for('main.perfil'))
            current_user.email = novo_email

        # 5. Localização e IBAN (Apenas para Produtores)
        if current_user.tipo == 'produtor':
            novo_iban = request.form.get('iban', '').replace(' ', '').upper()
            if novo_iban:
                current_user.iban = novo_iban

        prov_id = request.form.get('provincia_id')
        mun_id = request.form.get('municipio_id')
        if prov_id: current_user.provincia_id = int(prov_id)
        if mun_id: current_user.municipio_id = int(mun_id)

        # 6. Re-validar status do perfil
        current_user.verificar_e_atualizar_perfil()

        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"ERRO_EDITAR_PERFIL: {str(e)}")
        flash('Ocorreu um erro ao processar a atualização.', 'danger')

    return redirect(url_for('main.perfil'))

@auth_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    try:
        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmacao = request.form.get('confirmar_senha')

        # 1. Verificar se a senha atual está correta
        if not current_user.verificar_senha(senha_atual):
            flash('A palavra-passe atual está incorreta.', 'danger')
            return redirect(url_for('main.perfil'))

        # 2. Verificar se a nova senha e confirmação coincidem
        if nova_senha != confirmacao:
            flash('A nova palavra-passe e a confirmação não coincidem.', 'danger')
            return redirect(url_for('main.perfil'))

        # 3. Validar força mínima (ex: 6 caracteres)
        if len(nova_senha) < 6:
            flash('A nova palavra-passe deve ter pelo menos 6 caracteres.', 'warning')
            return redirect(url_for('main.perfil'))

        # 4. Atualizar e Guardar
        current_user.senha = nova_senha  # O seu modelo deve fazer o hash automaticamente
        db.session.commit()

        flash('Palavra-passe atualizada com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        print(f"ERRO ALTERAR SENHA: {e}")
        flash('Ocorreu um erro ao atualizar a palavra-passe.', 'danger')

    return redirect(url_for('main.perfil'))

