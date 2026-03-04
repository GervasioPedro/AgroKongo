from app import create_app
from app.extensions import db, get_celery  # Lazy loading do celery
from app.models import Transacao, Notificacao, TransactionStatus
from datetime import datetime, timezone
from markupsafe import escape

app = create_app()

# Obter instância do Celery (lazy loading)
celery = get_celery()


if celery is not None:
    @celery.task(name="tasks.auditoria_entregas")
    def job_verificar_entregas():
        """Tarefa agendada para confirmar entregas estagnadas."""
        with app.app_context():
            app.logger.info("--- Iniciando Auditoria de Entregas Automáticas ---")
            try:
                # Reutiliza a lógica robusta que definimos no Model Transacao
                count = Transacao.verificar_entregas_automaticas()

                db.session.commit()
                app.logger.info(f"--- Auditoria Concluída: {count} transações processadas ---")
                return f"{count} entregas verificadas."
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"❌ Erro na tarefa de auditoria: {str(e)}")
                raise e
else:
    # Celery não disponível (ex: erro Kerberos no Windows)
    def job_verificar_entregas():
        """Placeholder quando Celery não está disponível."""
        return "Celery não disponível"


def enviar_fatura_email(transacao_id):
    """Tarefa assíncrona para gerar e enviar fatura (não trava o Admin)."""
    with app.app_context():
        venda = Transacao.query.get(transacao_id)
        if not venda:
            return "Transação não encontrada."

        # Proteção XSS: escapar fatura_ref em logs
        app.logger.info(f"Gerando documentos para Ref: {escape(venda.fatura_ref)}")
        # Aqui integrarias com o WeasyPrint e Flask-Mail
        # Ex: enviar_email_com_anexo(venda.comprador.email, "Fatura AgroKongo", pdf_blob)
        return f"Documentos enviados para {escape(venda.comprador.email)}"

