import os
from flask import Flask, render_template, redirect, url_for # Removi a vírgula sobrando e adicionei redirect/url_for
from extensions import db, login_manager, migrate
from flask_login import login_required, current_user

def create_app():
    # 1. Configuração de Caminhos
    raiz_do_projeto = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(raiz_do_projeto, 'templates')
    static_dir = os.path.join(raiz_do_projeto, 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    # 2. Configurações do App
    app.config['SECRET_KEY'] = 'agro-kongo-secret-key-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrokongo.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 3. Inicialização de Extensões
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = 'auth.login'

    # 4. Rota Force Admin (DENTRO do create_app)
    @app.route('/admin-force')
    def force_admin():
        if current_user.is_authenticated:
            current_user.is_admin = True
            db.session.commit()
            # Usar HTML com link para facilitar o retorno
            return "Sucesso! Agora és Admin. <a href='/'>Voltar ao Início</a>"
        return "Erro: Precisas de fazer Login primeiro!"

    # 5. User Loader
    @login_manager.user_loader
    def load_user(usuario_id):
        from core.models import Usuario
        return Usuario.query.get(int(usuario_id))

    # 6. Filtros de Template
    @app.template_filter('formata_kz')
    def formata_kz(valor):
        try:
            valor = float(valor or 0)
            return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".") + " Kz"
        except (ValueError, TypeError):
            return "0,00 Kz"

    @app.template_filter('formata_kg')
    def formata_kg(valor):
        try:
            valor = float(valor or 0)
            if valor.is_integer(): return "{:,.0f}".format(valor).replace(",", ".") + " kg"
            return "{:,.1f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".") + " kg"
        except (ValueError, TypeError):
            return "0 kg"

    # 7. Handlers de Erro
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('erros/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('erros/404.html'), 404

    # 8. Registo de Blueprints
    from modules.publico.routes import publico_bp
    from modules.auth.routes import auth_bp
    from modules.mercado.routes import mercado_bp
    from modules.perfil.routes import perfil_bp
    from modules.admin.routes import admin_bp

    app.register_blueprint(publico_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(mercado_bp, url_prefix='/mercado')
    app.register_blueprint(perfil_bp, url_prefix='/perfil')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        db.create_all()

    return app

# Se este arquivo for executado diretamente
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)