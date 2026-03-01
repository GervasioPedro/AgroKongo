# app/tasks/__init__.py - Inicialização Celery + schedules centralizadas
# Versão Corrigida - 26/02/2026
from celery import Celery
from celery.schedules import crontab
from app.tasks.base import AgroKongoTask
from app.extensions import db, cache


def make_celery(app):
    """
    Cria instância Celery com contexto Flask.
    Todas as tasks herdam AgroKongoTask automaticamente.
    """
    celery = Celery(
        app.import_name,
        backend=app.config.get('REDIS_URL'),
        broker=app.config.get('REDIS_URL'),
        task_cls=AgroKongoTask  # ← Todas tasks herdam base automaticamente
    )

    celery.conf.update(
        app.config,
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='Africa/Luanda',
        enable_utc=True,
        broker_transport_options={'visibility_timeout': 3600},
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_reject_on_worker_lost=True,
        worker_max_tasks_per_child=100,
        task_default_queue='default'
    )

    # ==================== SCHEDULES CENTRALIZADAS ====================
    celery.conf.beat_schedule = {
        'monitorar-transacoes-estagnadas': {
            'task': 'app.tasks.monitorar_transacoes_estagnadas.monitorar_transacoes_estagnadas',
            'schedule': crontab(minute='*/30'),  # a cada 30 min
            'options': {'queue': 'maintenance_low'}
        },
        'limpar-transacoes-antigas': {
            'task': 'app.tasks.limpeza.limpar_transacoes_antigas',
            'schedule': crontab(hour=3, minute=15),  # 3:15 AM daily
            'options': {'queue': 'maintenance_low'}
        },
        'lembrete-pagamentos-pendentes': {
            'task': 'app.tasks.pagamentos.enviar_lembretes_pendentes',
            'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
            'options': {'queue': 'notifications_medium'}
        }
    }

    # ==================== LISTENERS PARA INVALIDAÇÃO DE CACHE ====================
    from sqlalchemy.event import listens_for
    from app.models import Transacao

    @listens_for(Transacao, 'after_insert')
    @listens_for(Transacao, 'after_update')
    @listens_for(Transacao, 'after_delete')
    def invalidate_relatorio_cache(mapper, connection, target):
        """Invalida cache de relatórios quando transações mudam."""
        try:
            # Opção 1: Limpar apenas relatórios (recomendado com Redis)
            cache.delete_matched('relatorio_financeiro_*')
        except AttributeError:
            # Fallback se Redis não suportar delete_matched
            cache.clear()

    return celery


# ==================== IMPORTS DE TODAS AS TASKS ====================
from app.tasks.pagamentos import processar_liquidacao
from app.tasks.faturas import gerar_pdf_fatura_assincrono
from app.tasks.relatorios import gerar_relatorio_excel_assincrono
from app.tasks.notificacoes import enviar_notificacao_externa
from app.tasks.limpeza import limpar_transacoes_antigas
from app.tasks.monitorar_transacoes_estagnadas import monitorar_transacoes_estagnadas

__all__ = [
    'make_celery',
    'processar_liquidacao',
    'gerar_pdf_fatura_assincrono',
    'gerar_relatorio_excel_assincrono',
    'enviar_notificacao_externa',
    'limpar_transacoes_antigas',
    'monitorar_transacoes_estagnadas'
]