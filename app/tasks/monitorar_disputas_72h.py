# app/tasks/monitorar_disputas_72h.py - Implementação RN04
# Task para detetar disputas automáticas após 72h sem confirmação
from celery import shared_task
from app.tasks.base import AgroKongoTask, AgroKongoTaskBase
from flask import current_app
from app.extensions import db
from app.models import Transacao, TransactionStatus, Notificacao, LogAuditoria
from datetime import datetime, timedelta, timezone


@shared_task(base=AgroKongoTaskBase, bind=True, max_retries=3)
def monitorar_disputas_72h(self):
    """
    RN04 - Disputa Automática:
    - Identifica transações enviadas há +72h sem confirmação
    - Impede liquidação automática
    - Alerta Admin sobre disputas potenciais
    """
    agora = datetime.now(timezone.utc)
    limite_disputa = agora - timedelta(hours=72)

    with current_app.app_context():
        try:
            # 1. Buscar transações ENVIADO há +72h sem confirmação
            disputas_pendentes = Transacao.query.filter(
                Transacao.status == TransactionStatus.ENVIADO,
                Transacao.data_envio <= limite_disputa
            ).all()

            if not disputas_pendentes:
                current_app.logger.info("✅ Nenhuma disputa de 72h detectada.")
                return

            # 2. Processar cada disputa potencial
            for transacao in disputas_pendentes:
                dias_atraso = (agora - transacao.data_envio).days
                
                # Marcar como disputa para bloquear liquidação
                transacao.status = TransactionStatus.DISPUTA
                
                # Log de auditoria
                db.session.add(LogAuditoria(
                    usuario_id=None,
                    acao="DISPUTA_AUTOMATICA_72H",
                    detalhes=f"Transação {transacao.fatura_ref} marcada como disputa após {dias_atraso} dias sem confirmação."
                ))
                
                # Alertar Admin
                db.session.add(Notificacao(
                    usuario_id=1,  # Admin principal
                    mensagem=f"⚠️ DISPUTA AUTOMÁTICA: {transacao.fatura_ref} enviada há {dias_atraso} dias sem confirmação. Intervenção necessária!",
                    link=f"/admin/resolver-disputa/{transacao.id}"
                ))
                
                # Notificar produtor sobre a disputa
                db.session.add(Notificacao(
                    usuario_id=transacao.vendedor_id,
                    mensagem=f"⚠️ Disputa automática iniciada para {transacao.fatura_ref}. Aguardando resolução administrativa.",
                    link="/produtor/vendas"
                ))
                
                # Notificar comprador sobre a disputa
                db.session.add(Notificacao(
                    usuario_id=transacao.comprador_id,
                    mensagem=f"⚠️ Encomenda {transacao.fatura_ref} em disputa automática. Por favor, confirme o recebimento ou contacte suporte.",
                    link="/comprador/minhas-compras"
                ))

            db.session.commit()
            current_app.logger.warning(
                f"🚨 {len(disputas_pendentes)} disputas automáticas de 72h processadas. Intervenção administrativa requerida."
            )

        except Exception as e:
            current_app.logger.critical(f"Erro crítico na task monitorar_disputas_72h: {e}", exc_info=True)
            db.session.rollback()
            raise self.retry(exc=e)
