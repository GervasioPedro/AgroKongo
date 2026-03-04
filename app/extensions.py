"""app/extensions.py
Extensões do Flask para AgroKongo.

Inclui: Database, Migration, CSRF, Login, Mail, Cache, Limiter.
(Celery com import lazy para evitar dependência de Kerberos no Windows)
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask import jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_caching import Cache

# Inicialização das extensões
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
cache = Cache()

# Celery - inicialização tardia (lazy) para evitar erro de Kerberos no Windows
celery = None
_celery_app = None


def get_celery():
    """Retorna instância do Celery (lazy loading para evitar erro gssapi/Kerberos)"""
    global _celery_app
    if _celery_app is None:
        try:
            from celery import Celery
            _celery_app = Celery(
                'agrokongo',
                broker=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
                backend=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
            )
        except OSError as e:
            # Se não conseguir importar (erro Kerberos), retorna None
            logging.warning(f"Celery não disponível: {e}")
            return None
    return _celery_app


def make_celery(app: Flask):
    """Configura Celery com contexto Flask"""
    celery_app = get_celery()
    if celery_app is None:
        return None
    
    celery_app.conf.update(
        broker_url=app.config.get('REDIS_URL'),
        result_backend=app.config.get('REDIS_URL'),
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Africa/Luanda',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutos
        task_soft_time_limit=25 * 60,
    )

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


def setup_extensions(app: Flask):
    """Configura todas as extensões com a aplicação Flask"""
    
    # Database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Security
    csrf.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    
    # Configure Login Manager
    login_manager.session_protection = "strong"
    # Keep login_view pointing to HTML endpoint for backwards compatibility
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para aceder a esta página."
    login_manager.login_message_category = "warning"

    @login_manager.unauthorized_handler
    def _unauthorized():
        """Retorno JSON para endpoints /api/*, evitando redirects e BuildError."""
        try:
            if request.path.startswith('/api/'):
                return jsonify({'ok': False, 'message': 'Nao autenticado.'}), 401
        except Exception:
            # fallback seguro
            pass
        # comportamento default do Flask-Login (redirect) para rotas HTML
        from flask_login import login_url
        from flask import redirect
        return redirect(login_url(login_manager.login_view, request.url))
    
    # Mail
    mail.init_app(app)
    
    # CORS
    CORS(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}}, supports_credentials=True)
    
    # Cache com Redis
    cache_config = {
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': app.config.get('REDIS_URL', 'redis://localhost:6379/1'),
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_KEY_PREFIX': 'agrokongo_',
    }
    cache.init_app(app, config=cache_config)
    
    # Celery
    # make_celery(app)  <-- COMENTADO
    
    # Logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/agrokongo.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AgroKongo Startup')
    
    # Rate Limiting - Configurações específicas
    limiter.enabled = not app.debug
    
    # Endpoints com rate limiting mais restritivo
    with app.app_context():
        from flask import request
        
        # Rate limit dinâmico baseado no IP
        @limiter.request_filter
        def ip_whitelist():
            return request.remote_addr in app.config.get('TRUSTED_IPS', [])
    
    app.logger.info("Extensões configuradas com sucesso")


# Decorator personalizado para rate limiting
def rate_limit(limit: str = "5 per minute"):
    """Decorator para aplicar rate limiting a rotas específicas"""
    return limiter.limit(limit)
