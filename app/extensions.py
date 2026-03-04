"""app/extensions.py
Extensões do Flask para AgroKongo.

Inclui: Database, Migration, CSRF, Login, Mail, Cache, Limiter.
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
