# celery_worker.py - Script de inicialização Celery custom (dev local + produção)
# Versão final corrigida - 22/02/2026 (leve, seguro e aconchegante)
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from celery import Celery
from app import create_app
from app.tasks import make_celery  # ← Novo make_celery com base profissional


def setup_worker_logging(level=logging.INFO):
    """Configuração de logging dedicado ao worker (alinhado com a app)"""
    logger = logging.getLogger('celery')
    logger.setLevel(level)

    if not os.path.exists('logs'):
        os.makedirs('logs', exist_ok=True)

    handler = RotatingFileHandler(
        'logs/celery_worker.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [Worker %(processName)s-%(process)d] %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Console colorido e amigável em dev (experiência inesquecível)
    if level == logging.DEBUG:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter(
            '\033[92m%(asctime)s\033[0m [\033[93m%(levelname)s\033[0m] %(message)s'
        ))
        logger.addHandler(console)


if __name__ == '__main__':  # ← Corrigido de 'if name == 'main''
    env = os.getenv('FLASK_ENV', 'development')
    app = create_app(env)

    with app.app_context():
        celery = make_celery(app)  # ← Usa o novo make_celery com AgroKongoTask + schedules

        # Queues isoladas (mantidas do teu original + alinhadas com as tasks novas)
        celery.conf.task_routes = {
            'app.tasks.faturas.*': {'queue': 'finance_high'},
            'app.tasks.pagamentos.*': {'queue': 'finance_high'},
            'app.tasks.relatorios.*': {'queue': 'reports'},
            'app.tasks.notificacoes.*': {'queue': 'notifications_medium'},
            'app.tasks.limpeza.*': {'queue': 'maintenance_low'},
            'app.tasks.monitorar_transacoes_estagnadas': {'queue': 'maintenance_low'},
            'app.tasks.monitoramento.*': {'queue': 'maintenance_low'}  # Novas tarefas de monitoramento
        }
        celery.conf.task_default_queue = 'default'

        # Tuning leve para dev / forte para produção
        celery.conf.worker_concurrency = int(os.getenv('CELERY_CONCURRENCY', os.cpu_count() or 4))
        celery.conf.worker_prefetch_multiplier = 1
        celery.conf.broker_transport_options = {'visibility_timeout': 3600}
        celery.conf.task_acks_late = True
        celery.conf.task_reject_on_worker_lost = True
        celery.conf.worker_max_tasks_per_child = 100

        setup_worker_logging(logging.DEBUG if app.debug else logging.INFO)

        app.logger.info("=" * 70)  # ← Corrigido '"= " * 70'
        app.logger.info(f"🚀 AGROKONGO CELERY WORKER INICIADO")  # ← Corrigido f-string
        app.logger.info(
            f"   Env: {env.upper()} | Concurrency: {celery.conf.worker_concurrency}")  # ← Corrigido f-string
        app.logger.info(
            f"   Queues: finance_high, reports, notifications_medium, maintenance_low, default")  # ← Corrigido 'repo rts'
        app.logger.info(
            f"   Beat schedules carregadas: {len(celery.conf.beat_schedule)} tarefas agendadas")  # ← Corrigido f-string
        app.logger.info("=" * 70)

        # WorkerCommand moderno e flexível
        from celery.bin.worker import WorkerCommand

        worker = WorkerCommand(app=celery)

        options = {
            'loglevel': 'DEBUG' if app.debug else 'INFO',  # ← Corrigido espaço
            'concurrency': celery.conf.worker_concurrency,
            'hostname': f'agrokongo_worker@{os.uname().nodename}',
            'queues': 'finance_high,reports,notifications_medium,maintenance_low,default',  # ← Corrigido 'repo rts'
            'beat': '--beat' in sys.argv,  # Suporte automático a beat
        }

        try:
            worker.run(**options)
        except Exception as e:  # ← Corrigido 'Excep tion'
            app.logger.critical(f"❌ Celery worker crash: {e}", exc_info=True)  # ← Corrigido f-string
            sys.exit(1)