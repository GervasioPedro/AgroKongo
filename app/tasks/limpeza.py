# app/tasks/limpeza.py - Versão auditada, eficiente e auditável (produção-ready)
# Versão Corrigida - 22/02/2026
from celery import shared_task
from app.extensions import db, current_app
from app.models import Transacao, TransactionStatus, LogAuditoria, Notificacao, Usuario  # ← Usuario adicionado
from app.utils.helpers import aware_utcnow  # ← Import adicionado
from datetime import timedelta
from sqlalchemy import and_, or_
from app.tasks.base import AgroKongoTask  # ← Import adicionado


@shared_task(bind=True, base=AgroKongoTask, max_retries=5, rate_limit='1/d')
def limpar_transacoes_antigas(self):
    """
    Limpeza async transações antigas (> config dias, FINALIZADO/CANCELADO).
    Segurança: soft delete atomic bulk; log/notificação admin.
    Performance: bulk update (eficiente escala); índice recomendado.
    """
    try:
        dias = int(current_app.config.get('LIMPEZA_DIAS_TRANSACOES', 180))
        limite = aware_utcnow() - timedelta(days=dias)
        
        count = _contar_transacoes_antigas(limite)
        if count == 0:
            current_app.logger.info("Limpeza transações: nenhuma encontrada.")
            return "Nenhuma transação para limpar"
        
        updated = _executar_limpeza(limite)
        _registrar_auditoria_limpeza(updated, dias, self.request.id)
        _notificar_admin_sucesso(updated, dias)
        
        current_app.logger.info(f"Limpeza transações concluída: {updated} afetadas.")
        return f"Limpas {updated} transações"

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro task limpeza transações (ID: {self.request.id}): {e}", exc_info=True)
        _notificar_admin_erro(self.request.id, e)
        raise self.retry(exc=e)


def _criar_filtro_transacoes_antigas(limite):
    """Cria filtro para transações antigas."""
    return and_(
        Transacao.status.in_([TransactionStatus.FINALIZADO, TransactionStatus.CANCELADO]),
        Transacao.is_active is True,
        or_(
            Transacao.data_liquidacao < limite,
            and_(Transacao.data_liquidacao.is_(None), Transacao.data_criacao < limite)
        )
    )


def _contar_transacoes_antigas(limite):
    """Conta transações antigas que serão limpas."""
    filtro = _criar_filtro_transacoes_antigas(limite)
    return db.session.query(Transacao).filter(filtro).count()


def _executar_limpeza(limite):
    """Executa soft delete em bulk das transações antigas."""
    filtro = _criar_filtro_transacoes_antigas(limite)
    updated = db.session.query(Transacao).filter(filtro).update(
        {Transacao.is_active: False},
        synchronize_session=False
    )
    db.session.commit()
    return updated


def _registrar_auditoria_limpeza(updated, dias, task_id):
    """Registra auditoria da limpeza."""
    db.session.add(LogAuditoria(
        usuario_id=None,
        acao="LIMPEZA_TRANSACOES_ANTIGAS",
        detalhes=f"Limpas {updated} transações antigas (> {dias} dias) - task {task_id}"
    ))
    db.session.commit()


def _notificar_admin_sucesso(updated, dias):
    """Notifica administrador sobre limpeza bem-sucedida."""
    admin = db.session.query(Usuario).filter_by(tipo='admin').first()
    if admin:
        db.session.add(Notificacao(
            usuario_id=admin.id,
            mensagem=f"Limpeza automática: {updated} transações antigas arquivadas (> {dias} dias).",
            categoria='manutencao_sistema'
        ))
        db.session.commit()


def _notificar_admin_erro(task_id, erro):
    """Notifica administrador sobre erro na limpeza."""
    admin = db.session.query(Usuario).filter_by(tipo='admin').first()
    if admin:
        db.session.add(Notificacao(
            usuario_id=admin.id,
            mensagem=f"Erro limpeza transações automáticas (task {task_id}): {str(erro)[:100]}...",
            categoria='erro_manutencao'
        ))
        db.session.commit()