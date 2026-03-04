import os
from flask import Flask, send_from_directory, abort
from flask_login import login_required, current_user
from flask_apscheduler import APScheduler
from datetime import datetime, timezone, timedelta
from flask_talisman import Talisman
from app.extensions import db, setup_extensions
from app.models import Transacao, TransactionStatus
from config import config_dict
from app.middleware import ProxyFix

scheduler = APScheduler()

def processar_monitorizacao_pagamentos(app):
    """Auditoria automática para evitar que transações fiquem 'esquecidas'."""
    with app.app_context():
        agora = datetime.now(timezone.utc)
        limite = agora - timedelta(hours=24)
        try:
            estagnadas = Transacao.query.filter(
                Transacao.status == TransactionStatus.ANALISE,
                Transacao.data_criacao <= limite
            ).all()

            for t in estagnadas:
                app.logger.warning(f"AUDITORIA: Fatura {t.fatura_ref} em análise há mais de 24h.")

        except Exception as e:
            app.logger.error(f"Erro no Scheduler: {e}")

def create_app(config_name='dev'):
    app = Flask(__name__)
    app.config.from_object(config_dict[config_name])
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    # Aplicar ProxyFix em produção
    if not app.debug:
        app.wsgi_app = ProxyFix(app.wsgi_app)

    setup_extensions(app)

    # Context processors for template variables
    @app.context_processor
    def inject_globals():
        return {
            'agora': datetime.now(timezone.utc),
            'TStatus': TransactionStatus,
            'now': datetime.now(),
            'timedelta': timedelta
        }

    # Aplicar headers de segurança e HTTPS/HSTS em produção
    if not app.debug:
        csp = {
            'default-src': ["'self'"],
            'script-src': ["'self'"], # Removido 'unsafe-inline'
            'style-src': ["'self'"],  # Removido 'unsafe-inline'
            'img-src': ["'self'", 'data:', 'https:'],
            'connect-src': ["'self'", *app.config.get('CORS_ORIGINS', [])],
            'font-src': ["'self'", 'data:'],
            'frame-ancestors': ["'self'"],
            'object-src': ["'none'"], # Adicionado para bloquear plugins
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
    """Registra todos os blueprints da aplicação."""
    from app.routes.main_fixed import main_bp
    from app.routes.auth import auth_bp
    from app.routes.produtor import produtor_bp
    from app.routes.mercado import mercado_bp
    from app.routes.comprador import comprador_bp
    from app.routes.admin import admin_bp
    from app.routes.api_public import api_public_bp
    from app.routes.api_cadastro import api_cadastro_bp
    from app.routes.geografia import geografia_bp
    from app.routes.api_v1 import api_v1_bp
    # Novos blueprints API JSON
    try:
        from app.routes.mercado_api import mercado_api_bp
    except Exception:
        mercado_api_bp = None
    try:
        from app.routes.comprador_api import comprador_api_bp
    except Exception:
        comprador_api_bp = None
    # Redirecionamentos de rotas HTML legadas para o SPA
    try:
        from app.routes.legacy_redirects import legacy_redirects_bp
    except Exception:
        legacy_redirects_bp = None

    # Error handlers blueprint (JSON para /api/*)
    try:
        from app.routes.handlers import errors_bp
    except Exception:
        errors_bp = None

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(produtor_bp)
    app.register_blueprint(mercado_bp)
    app.register_blueprint(comprador_bp)
    app.register_blueprint(admin_bp)  # Rotas já incluem /api/admin no arquivo admin.py
    app.register_blueprint(api_public_bp)
    app.register_blueprint(api_cadastro_bp)
    app.register_blueprint(geografia_bp)
    app.register_blueprint(api_v1_bp)
    if mercado_api_bp:
        app.register_blueprint(mercado_api_bp)
    if comprador_api_bp:
        app.register_blueprint(comprador_api_bp)
    if legacy_redirects_bp:
        app.register_blueprint(legacy_redirects_bp)
    if errors_bp:
        app.register_blueprint(errors_bp)

def _criar_diretorios(app):
    with app.app_context():
        pastas = [
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'safras'),
            os.path.join(app.config['UPLOAD_FOLDER_PUBLIC'], 'perfil'),
            os.path.join(app.config['UPLOAD_FOLDER_PRIVATE'], 'comprovativos'),
        ]
        for pasta in pastas:
            os.makedirs(pasta, exist_ok=True)

def _configurar_scheduler(app):
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if not scheduler.running:
            scheduler.init_app(app)
            scheduler.add_job(
                id='audit_pagamentos',
                func=processar_monitorizacao_pagamentos,
                args=[app],
                trigger='interval',
                hours=1
            )
            scheduler.start()
