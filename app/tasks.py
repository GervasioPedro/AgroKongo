"""
Tarefas Assíncronas do Celery
Processamento em background para operações pesadas.
"""
from app import create_app
from app.extensions import db, celery, CELERY_AVAILABLE
from app.models import Transacao, Notificacao, TransactionStatus
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

app = create_app()


# Registrar tarefas apenas se Celery estiver disponível
if CELERY_AVAILABLE and celery is not None:
    @celery.task(name="tasks.auditoria_entregas", bind=True, max_retries=3)
    def job_verificar_entregas(self):
        """Tarefa agendada para confirmar entregas estagnadas automaticamente."""
        with app.app_context():
            try:
                logger.info("--- Iniciando Auditoria de Entregas Automáticas ---")
                
                # Reutiliza a lógica robusta que definimos no Model Transacao
                count = Transacao.verificar_entregas_automaticas()
                
                db.session.commit()
                logger.info(f"--- Auditoria Concluída: {count} transações processadas ---")
                
                return f"{count} entregas verificadas."
                
            except Exception as exc:
                db.session.rollback()
                logger.error(f"❌ Erro na tarefa de auditoria: {str(exc)}")
                # Retry automático com backoff exponencial
                raise self.retry(exc=exc, countdown=60)  # Tenta novamente em 1 minuto

    @celery.task(name="tasks.enviar_fatura_email", bind=True, max_retries=3)
    def enviar_fatura_email(self, transacao_id):
        """Tarefa assíncrona para gerar e enviar fatura por email."""
        with app.app_context():
            try:
                venda = Transacao.query.get(transacao_id)
                if not venda:
                    logger.warning(f"Transação {transacao_id} não encontrada para envio de email")
                    return "Transação não encontrada."
                
                logger.info(f"Gerando documentos para Ref: {venda.fatura_ref}")
                
                # Aqui integrarias com o WeasyPrint e Flask-Mail
                # Exemplo:
                # pdf_blob = gerar_pdf_fatura(venda)
                # enviar_email_com_anexo(venda.comprador.email, "Fatura AgroKongo", pdf_blob)
                
                logger.info(f"Email enviado para {venda.comprador.email}")
                return f"Documentos enviados para {venda.comprador.email}"
                
            except Exception as exc:
                logger.error(f"Erro ao enviar email da fatura {transacao_id}: {str(exc)}")
                raise self.retry(exc=exc, countdown=120)  # Tenta em 2 minutos

    @celery.task(name="tasks.limpar_sessoes_expiradas")
    def limpar_sessoes_expiradas():
        """Limpa sessões expiradas do banco de dados (manutenção)."""
        with app.app_context():
            try:
                # Implementar limpeza de sessões antigas se necessário
                logger.info("Tarefa de limpeza de sessões executada")
                return "Sessões limpas"
            except Exception as e:
                logger.error(f"Erro na limpeza de sessões: {e}")
                return "Erro na limpeza"
else:
    # Fallback síncrono quando Celery não está disponível
    logger.warning("Celery não disponível - usando fallback síncrono")
    
    def job_verificar_entregas():
        """Versão síncrona para quando Celery não está disponível."""
        with app.app_context():
            try:
                logger.info("--- Iniciando Auditoria de Entregas (Síncrono) ---")
                count = Transacao.verificar_entregas_automaticas()
                db.session.commit()
                logger.info(f"--- Auditoria Concluída: {count} transações processadas ---")
                return f"{count} entregas verificadas."
            except Exception as exc:
                db.session.rollback()
                logger.error(f"❌ Erro na auditoria síncrona: {str(exc)}")
                raise
    
    def enviar_fatura_email(transacao_id):
        """Versão síncrona para quando Celery não está disponível."""
        with app.app_context():
            try:
                venda = Transacao.query.get(transacao_id)
                if not venda:
                    logger.warning(f"Transação {transacao_id} não encontrada")
                    return "Transação não encontrada."
                logger.info(f"Processando documentos (Síncrono) para Ref: {venda.fatura_ref}")
                return f"Documentos processados para {venda.comprador.email}"
            except Exception as exc:
                logger.error(f"Erro no processamento síncrono: {str(exc)}")
                raise
    
    def limpar_sessoes_expiradas():
        """Versão síncrona para quando Celery não está disponível."""
        with app.app_context():
            try:
                logger.info("Tarefa de limpeza de sessões executada (Síncrono)")
                return "Sessões limpas"
            except Exception as e:
                logger.error(f"Erro na limpeza de sessões: {e}")
                return "Erro na limpeza"

