from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import MetaData
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
import os
from celery import Celery
# Convenção rigorosa: Crucial para migrações sem errors entre SQLite/PostgreSQL
convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)



db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()
login_manager = LoginManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
celery = Celery(__name__)

def setup_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)

    # Configuração do Celery
    celery.conf.update(
        broker_url=app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        result_backend=app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        task_ignore_result=True
    )

    # Segurança de Sessão Industrial
    login_manager.session_protection = "strong"
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para aceder a esta página."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario  # Import interno para evitar ciclos
        return Usuario.query.get(int(user_id))

    # Configuração de Logs de Auditoria (Essencial para o AgroKongo)
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        # Mantém 10 ficheiros de log de 10MB cada (rotação para não encher o disco)
        file_handler = RotatingFileHandler('logs/agrokongo.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AgroKongo Startup - Sistema de Monitorização Ativado')




