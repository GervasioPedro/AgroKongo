from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import MetaData
from flask_mail import Mail
import logging
from logging.handlers import RotatingFileHandler
import os

# Import lazy do Celery para evitar falha no Windows por gssapi/Kerberos
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except (OSError, ImportError):
    # Fallback para ambientes sem Kerberos (Windows sem KfW)
    Celery = None
    CELERY_AVAILABLE = False
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

# Inicializa Celery apenas se disponível
if CELERY_AVAILABLE and Celery is not None:
    celery = Celery(__name__)  # Iniciamos com o nome do módulo
else:
    celery = None  # Fallback para quando Celery não está disponível

def setup_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # Configuração Robusta do Celery para Produção (apenas se disponível)
    if CELERY_AVAILABLE and celery is not None:
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        celery.conf.update(
            broker_url=redis_url,
            result_backend=redis_url,
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=300,  # Timeout de 5 minutos para tarefas
            worker_prefetch_multiplier=1,  # Processa uma tarefa por vez (evita memory leaks)
            broker_transport_options={'visibility_timeout': 3600},  # 1 hora
            broker_connection_retry_on_startup=True,
            worker_send_task_events=True,  # Para monitoramento com Flower
            task_send_sent_event=True,
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




