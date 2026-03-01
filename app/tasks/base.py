# app/tasks/base.py - Task base profissional (usada por TODAS as tasks)
# Versão Corrigida - 26/02/2026
import logging
from celery import Task
from flask import current_app
from app.extensions import db
from app.models import Usuario, Notificacao
import bleach

logger = logging.getLogger(__name__)


class AgroKongoTask(Task):
    """
    Base para todas as tasks: contexto Flask + retry + limpeza + auditoria.
    Todas as tasks Celery devem herdar desta classe para consistência.
    """
    abstract = True
    autoretry_for = (Exception,)
    max_retries = 5
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True

    def __call__(self, *args, **kwargs):
        """Garante contexto Flask em todas as tasks."""
        with current_app.app_context():
            return super().__call__(*args, **kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Handler de falha: log seguro + notifica admin.
        Sanitiza exceção para prevenir XSS nos logs.
        """
        safe_exc = bleach.clean(str(exc)[:500], tags=[], strip=True)
        logger.error(f"Task {self.name} (ID: {task_id}) falhou: {safe_exc}", exc_info=einfo)

        try:
            with current_app.app_context():
                admin = db.session.query(Usuario).filter_by(tipo='admin').first()
                if admin:
                    db.session.add(Notificacao(
                        usuario_id=admin.id,
                        mensagem=f"⚠️ Task Celery falhou: {self.name} (ID: {task_id}) - {safe_exc[:100]}...",
                        link="/admin/dashboard"
                    ))
                    db.session.commit()
        except Exception as e:
            logger.error(f"Erro ao notificar admin sobre falha de task: {e}")
            db.session.rollback()

        super().on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Cleanup após task completar (sucesso ou falha).
        Garante que sessions DB não vazem.
        """
        try:
            db.session.rollback()
            db.session.remove()
        except Exception as e:
            logger.warning(f"Erro ao limpar session DB: {e}")

        super().after_return(status, retval, task_id, args, kwargs, einfo)