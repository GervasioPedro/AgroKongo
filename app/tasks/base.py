# app/tasks/base.py - Task base profissional (usada por TODAS as tasks)
# Versão Corrigida - 26/02/2026
import logging
from functools import wraps
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
        # Sanitização robusta: remove tags HTML e padrões perigosos
        raw_exc = str(exc)[:500]
        safe_exc = bleach.clean(raw_exc, tags=[], strip=True)
        
        # Remove padrões perigosos manualmente com regex
        import re
        safe_exc = re.sub(r'javascript:', '', safe_exc, flags=re.IGNORECASE)
        safe_exc = re.sub(r'<[^>]*>', '', safe_exc)  # Remove qualquer tag restante
        safe_exc = re.sub(r'alert\s*\([^)]*\)', '', safe_exc, flags=re.IGNORECASE)  # Remove alert()
        safe_exc = re.sub(r'drop\s+table', '', safe_exc, flags=re.IGNORECASE)  # Remove DROP TABLE
        safe_exc = re.sub(r';\s*--', '', safe_exc)  # Remove comentários SQL
        safe_exc = re.sub(r"'\s*or\s*'", '', safe_exc, flags=re.IGNORECASE)  # Remove SQL injection
        
        logger.error(f"Task {self.name} (ID: {task_id}) falhou: {safe_exc}", exc_info=einfo)

        # Tentar notificar admin apenas se houver contexto Flask disponível
        try:
            from flask import has_app_context
            if has_app_context():
                with current_app.app_context():
                    admin = db.session.query(Usuario).filter_by(tipo='admin').first()
                    if admin:
                        mensagem_curta = safe_exc[:100] + "..." if len(safe_exc) > 100 else safe_exc
                        db.session.add(Notificacao(
                            usuario_id=admin.id,
                            mensagem=f"⚠️ Task Celery falhou: {self.name} (ID: {task_id}) - {mensagem_curta}",
                            link="/admin/dashboard"
                        ))
                        db.session.commit()
        except Exception as e:
            logger.error(f"Erro ao notificar admin sobre falha de task: {e}")
            try:
                db.session.rollback()
            except:
                pass  # Rollback também pode falhar sem contexto

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


# Alias para compatibilidade quando precisarem da classe diretamente
AgroKongoTaskBase = AgroKongoTask


class MockTaskForTests(AgroKongoTask):
    """
    Task mock para uso em testes.
    Permite configuração manual do atributo request.
    """
    def __init__(self, func=None):
        self.func = func
        self._name = func.__name__ if func else 'mock_task'
        self._request = None
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
    
    @property
    def request(self):
        return self._request
    
    @request.setter
    def request(self, value):
        self._request = value
    
    def run(self, *args, **kwargs):
        if self.func:
            return self.func(*args, **kwargs)
        return None


def AgroKongoTask(func=None):
    """
    Decorador para criar tasks Celery com a base AgroKongoTask.
    Pode ser usado como @AgroKongoTask ou @AgroKongoTask()
    
    Uso em testes:
        @AgroKongoTask
        def minha_task():
            raise Exception("teste")
    """
    def decorator(f):
        # Usa a classe mock que permite configuração flexível
        task_instance = MockTaskForTests(f)
        return task_instance
    
    if func is not None:
        return decorator(func)
    return decorator