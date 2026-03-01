# app/tasks/monitorar_transacoes_estagnadas.py - Versão auditada, resiliente e automática
# Versão Corrigida - 22/02/2026
from celery import shared_task
from app.tasks.base import AgroKongoTask  # ← Import adicionado
from app.extensions import db, current_app
from app.models import Transacao, TransactionStatus, Notificacao, Safra, LogAuditoria, Usuario  # ← Usuario adicionado
from datetime import datetime, timedelta, timezone
from flask import url_for  # ← Import adicionado


@shared_task(base=AgroKongoTask, bind=True, max_retries=3)
def monitorar_transacoes_estagnadas(self):
    """
    Motor de integridade do AgroKongo:
    - Notifica admins sobre atrasos na validação (24h)
    - Cancela reservas não pagas automaticamente e devolve stock (48h)
    - Registra auditoria de todas as ações
    """
    with current_app.app_context():
        try:
            agora = datetime.now(timezone.utc)
            _alertar_admin_transacoes_atrasadas(agora)
            canceladas = _cancelar_reservas_expiradas(agora)
            _registrar_resultado_monitorizacao(canceladas)
            
        except Exception as e:
            current_app.logger.critical(f"Erro crítico na task monitorar_transacoes_estagnadas: {e}", exc_info=True)
            db.session.rollback()
            raise self.retry(exc=e)


def _alertar_admin_transacoes_atrasadas(agora):
    """Alerta administradores sobre transações em análise há mais de 24h."""
    limite_analise = agora - timedelta(hours=24)
    
    estagnadas_admin = Transacao.query.filter(
        Transacao.status == TransactionStatus.ANALISE,
        Transacao.data_criacao <= limite_analise
    ).all()

    for t in estagnadas_admin:
        current_app.logger.warning(f"⚠️ ADMIN_DELAY: Ref {t.fatura_ref} em análise há +24h")
        db.session.add(Notificacao(
            usuario_id=1,
            mensagem=f"🔔 Transação {t.fatura_ref} está em análise há mais de 24h. Verifique urgente!",
            link=f"/admin/detalhe-transacao/{t.id}"
        ))
    
    db.session.commit()


def _cancelar_reservas_expiradas(agora):
    """Cancela reservas não pagas após 48h e devolve stock."""
    limite_expiracao = agora - timedelta(hours=48)
    
    reservas_expiradas = Transacao.query.filter(
        Transacao.status == TransactionStatus.PENDENTE,
        Transacao.data_criacao <= limite_expiracao
    ).all()

    canceladas_count = 0
    for t in reservas_expiradas:
        if _processar_cancelamento_reserva(t):
            canceladas_count += 1
    
    db.session.commit()
    return canceladas_count


def _processar_cancelamento_reserva(transacao):
    """Processa cancelamento de uma reserva individual."""
    try:
        _devolver_stock_safra(transacao)
        transacao.status = TransactionStatus.CANCELADO
        _notificar_comprador_expiracao(transacao)
        _registrar_auditoria_cancelamento(transacao)
        return True
        
    except Exception as e:
        current_app.logger.error(f"Erro ao cancelar transação {transacao.id}: {e}")
        db.session.rollback()
        return False


def _devolver_stock_safra(transacao):
    """Devolve stock ao produtor."""
    safra = Safra.query.get(transacao.safra_id)
    if safra:
        safra.quantidade_disponivel += transacao.quantidade_comprada
        if safra.quantidade_disponivel > 0 and safra.status == 'esgotado':
            safra.status = 'disponivel'


def _notificar_comprador_expiracao(transacao):
    """Notifica comprador sobre expiração da reserva."""
    db.session.add(Notificacao(
        usuario_id=transacao.comprador_id,
        mensagem=f"🌱 Sua reserva {transacao.fatura_ref} expirou por falta de pagamento. O stock já voltou ao produtor. Pode comprar novamente!",
        link="/mercado"
    ))


def _registrar_auditoria_cancelamento(transacao):
    """Registra auditoria do cancelamento automático."""
    db.session.add(LogAuditoria(
        usuario_id=None,
        acao="AUTO_CANCEL",
        detalhes=f"Reserva {transacao.fatura_ref} cancelada automaticamente após 48h. Stock devolvido."
    ))


def _registrar_resultado_monitorizacao(canceladas_count):
    """Registra resultado da monitorização no log."""
    if canceladas_count > 0:
        current_app.logger.info(f"♻️ Limpeza automática concluída: {canceladas_count} reservas canceladas e stock libertado.")
    else:
        current_app.logger.info("✅ Nenhuma transação estagnada encontrada.")