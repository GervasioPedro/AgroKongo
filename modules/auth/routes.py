from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from core.models import Usuario, Provincia, Municipio
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)


def redirect_por_tipo(usuario_obj):
    """
    Direciona o utilizador para a página correta conforme o seu papel e estado do perfil.
    """
    # 1. Se o nome não estiver preenchido, obriga a completar perfil
    if not usuario_obj.nome:
        return redirect(url_for('auth.completar_perfil'))

    # 2. Se for administrador, vai para a gestão
    if getattr(usuario_obj, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))

    # 3. Lógica de Negócio: Produtor vai para Gestão, Comprador vai para Mercado
    if usuario_obj.tipo == 'produtor':
        return redirect(url_for('perfil.meu_perfil_produtor'))

    return redirect(url_for('mercado.explorar'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_por_tipo(current_user)

    if request.method == 'POST':
        telemovel = request.form.get('telemovel', '').strip()
        senha = request.form.get('senha', '')

        usuario = Usuario.query.filter_by(telemovel=telemovel).first()

        if usuario and check_password_hash(usuario.senha_hash, senha):
            login_user(usuario)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                return redirect_por_tipo(usuario)
            return redirect(next_page)

        flash('Telemóvel ou senha incorretos.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/cadastro', defaults={'tipo': None}, methods=['GET', 'POST'])
@auth_bp.route('/cadastro/<tipo>', methods=['GET', 'POST'])
def cadastro(tipo):
    if current_user.is_authenticated:
        return redirect_por_tipo(current_user)

    if tipo is None:
        return render_template('auth/escolher_perfil.html')

    if tipo not in ['produtor', 'comprador']:
        return redirect(url_for('auth.cadastro'))

    provincias = Provincia.query.order_by(Provincia.nome).all()

    if request.method == 'POST':
        telemovel = request.form.get('telemovel', '').strip()
        senha = request.form.get('senha', '')
        # Certifique-se que o 'name' no HTML é 'provincia'
        provincia_id_form = request.form.get('provincia')

        # DEBUG: Veja no terminal se o ID aparece ou se aparece None
        print(f"DEBUG CADASTRO: Recebido provincia_id = {provincia_id_form}")

        if len(telemovel) < 9:
            flash('Número de telemóvel inválido.', 'warning')
            return redirect(url_for('auth.cadastro', tipo=tipo))

        if Usuario.query.filter_by(telemovel=telemovel).first():
            flash('Este número já está registado.', 'error')
            return redirect(url_for('auth.cadastro', tipo=tipo))

        # Garantir que provincia_id é tratado corretamente
        p_id = None
        if provincia_id_form and str(provincia_id_form).isdigit():
            p_id = int(provincia_id_form)

        novo_usuario = Usuario(
            telemovel=telemovel,
            senha_hash=generate_password_hash(senha),
            provincia_id=p_id,
            tipo=tipo,
            nome=None,  # Garante que inicia como None para cair no completar_perfil
            municipio_id=None
        )

        try:
            db.session.add(novo_usuario)
            db.session.commit()

            # Forçamos o login e garantimos que a sessão reconhece os dados
            login_user(novo_usuario)

            # DEBUG: Confirmar se gravou no banco antes de redirecionar
            print(f"USUÁRIO CRIADO: ID {novo_usuario.id}, Província {novo_usuario.provincia_id}")

            flash('Bem-vindo(a)! Complete o seu perfil para continuar.', 'success')
            return redirect(url_for('auth.completar_perfil'))
        except Exception as e:
            db.session.rollback()
            print(f"ERRO AO CRIAR CONTA: {e}")
            flash('Erro ao criar conta. Tente novamente.', 'danger')

    return render_template(f'auth/cadastrar_{tipo}.html', provincias=provincias, tipo=tipo)


@auth_bp.route('/completar-perfil', methods=['GET', 'POST'])
@login_required
def completar_perfil():
    if request.method == 'POST':
        try:
            # Captura dos dados básicos
            current_user.nome = request.form.get('nome')
            current_user.nif = request.form.get('nif')

            # Localização
            provincia_id = request.form.get('provincia_id')
            municipio_id = request.form.get('municipio_id')

            if provincia_id:
                current_user.provincia_id = int(provincia_id)
            if municipio_id:
                current_user.municipio_id = int(municipio_id)

            current_user.referencia = request.form.get('referencia')

            # Campo exclusivo para Produtores (Opcional ou obrigatório dependendo da tua regra)
            if current_user.tipo == 'produtor':
                current_user.iban = request.form.get('iban')

            db.session.commit()
            flash('Perfil completado com sucesso! Bem-vindo ao AgroKongo.', 'success')
            return redirect(url_for('perfil.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar os dados. Verifique se o NIF ou IBAN já estão registados.', 'danger')
            print(f"Erro no completar_perfil: {e}")

    provincias = Provincia.query.order_by(Provincia.nome).all()
    return render_template('auth/completar_perfil.html', provincias=provincias)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão terminada.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/ativar-meu-acesso-admin-secreto')
@login_required
def tornar_admin():
    # Esta rota transforma o utilizador logado em Admin
    current_user.is_admin = True
    db.session.commit()
    flash("Acesso Administrativo ativado com sucesso! Agora já podes ver o painel.", "success")
    return redirect(url_for('perfil.dashboard'))