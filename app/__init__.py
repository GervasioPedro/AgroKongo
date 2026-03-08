import os
from flask import Flask
from flask_apscheduler import APScheduler
from flask_talisman import Talisman
from datetime import datetime, timezone, timedelta

from app.extensions import db, setup_extensions
from config import config_dict
from app.middleware import ProxyFix

scheduler = APScheduler()

def create_app(config_name='dev', test_config_override=None):
    app = Flask(__name__)

    if test_config_override:
        app.config.from_mapping(test_config_override)
    else:
        app.config.from_object(config_dict[config_name])

    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # ProxyFix deve ser aplicado apenas em produção
    if not app.config.get('TESTING') and not app.debug:
        app.wsgi_app = ProxyFix(app.wsgi_app)

    # Inicializar extensões com a app
    setup_extensions(app)

    @app.context_processor
    def inject_globals():
        return {
            'agora': datetime.now(timezone.utc),
            'now': datetime.now(),
            'timedelta': timedelta
        }

    if not app.config.get('TESTING') and not app.debug:
        csp = {
            'default-src': ["'self'"],
            'script-src': ["'self'"],
            'style-src': ["'self'"],
            'img-src': ["'self'", 'data:', 'https:'],
            'connect-src': ["'self'", *app.config.get('CORS_ORIGINS', [])],
            'font-src': ["'self'", 'data:'],
            'frame-ancestors': ["'self'"],
            'object-src': ["'none'"],
        }
        Talisman(
            app,
            force_https=True,
            strict_transport_security=True,
            strict_transport_security_max_age=31536000,
            strict_transport_security_include_subdomains=True,
            content_security_policy=csp,
            session_cookie_secure=True,
            session_cookie_http_only=True,
            frame_options='DENY',
            referrer_policy='no-referrer'
        )

    _registrar_blueprints(app)
    _criar_diretorios(app)
    _configurar_scheduler(app)

    return app

def _registrar_blueprints(app):
    # Importar apenas os blueprints principais e consolidados
    from app.routes.auth import auth_bp
    from app.routes.produtor import produtor_bp
    from app.routes.mercado import mercado_bp
    from app.routes.comprador import comprador_bp
    from app.routes.admin import admin_bp
    from app.routes.api_public import api_public_bp
    from app.routes.api_cadastro import api_cadastro_bp
    from app.routes.geografia import geografia_bp
    from app.routes.handlers import errors_bp
    
    # Tentar importar legacy apenas se existir (para compatibilidade)
    try:
        from app.routes.legacy_redirects import legacy_redirects_bp
        app.register_blueprint(legacy_redirects_bp)
    except ImportError:
        pass

    app.register_blueprint(auth_bp)
    app.register_blueprint(produtor_bp)
    app.register_blueprint(mercado_bp)
    app.register_blueprint(comprador_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_public_bp)
    app.register_blueprint(api_cadastro_bp)
    app.register_blueprint(geografia_bp)
    app.register_blueprint(errors_bp)

def _criar_diretorios(app):
    if not app.config.get('TESTING'):
        pastas = [
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'safras'),
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil'),
            os.path.join(app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos'),
        ]
        for pasta in pastas:
            os.makedirs(pasta, exist_ok=True)

def _configurar_scheduler(app):
    if not app.debug and not app.config.get('TESTING'):
        if not scheduler.running:
            scheduler.init_app(app)
            # ... (jobs)
            scheduler.start()
