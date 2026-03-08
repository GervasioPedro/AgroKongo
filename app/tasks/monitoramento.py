"""
Tarefa Celery para Monitorização de Pagamentos
Substitui o scheduler APScheduler anterior
"""
from celery import shared_task
from flask import current_app
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def monitorar_pagamentos_periodico(self):
    """
    Tarefa periódica para monitorizar pagamentos no escrow.
    Executa a cada hora automaticamente via Celery Beat.
    
    Esta tarefa substitui o job do APScheduler que rodava no processo web.
    Agora roda em worker separado, melhorando performance e escalabilidade.
    """
    try:
        # Import delayed para evitar circular imports
        from app.tasks.faturas import processar_monitorizacao_pagamentos
        
        logger.info("Iniciando monitorização periódica de pagamentos...")
        
        # Executar monitorização
        resultados = processar_monitorizacao_pagamentos()
        
        logger.info(f"Monitorização concluída. Resultados: {resultados}")
        
        return {
            'status': 'success',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'resultados': resultados
        }
        
    except Exception as exc:
        logger.error(f"Erro na monitorização de pagamentos: {str(exc)}")
        
        # Retry com backoff exponencial
        raise self.retry(exc=exc, countdown=300)  # Retry em 5 minutos


@shared_task(bind=True, max_retries=3)
def limpar_transacoes_antigas(self):
    """
    Tarefa periódica para limpar transações antigas/canceladas.
    Executa diariamente às 3 AM.
    """
    try:
        from app.models import Transacao
        from app.models.base import TransactionStatus
        from datetime import timedelta
        
        logger.info("Limpando transações antigas...")
        
        # Transações canceladas há mais de 90 dias
        limite = datetime.now(timezone.utc) - timedelta(days=90)
        
        transacoes_antigas = Transacao.query.filter(
            Transacao.status == TransactionStatus.CANCELADO,
            Transacao.data_criacao < limite
        ).all()
        
        count = len(transacoes_antigas)
        
        # Em produção, faríamos delete ou archive
        # Por enquanto, apenas logamos
        logger.info(f"Encontradas {count} transações antigas para limpeza")
        
        return {
            'status': 'success',
            'transacoes_encontradas': count,
            'limite_data': limite.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Erro na limpeza de transações: {str(exc)}")
        raise self.retry(exc=exc, countdown=600)


@shared_task(bind=True, max_retries=3)
def enviar_relatorios_diarios(self):
    """
    Tarefa para enviar relatórios diários por email.
    Executa diariamente às 8 AM.
    """
    try:
        from app.tasks.relatorios import gerar_relatorio_excel_assincrono
        from app.models import Usuario
        
        logger.info("Gerando relatórios diários...")
        
        # Buscar admins para enviar relatórios
        admins = Usuario.query.filter_by(tipo='admin', ativo=True).all()
        
        for admin in admins:
            # Gerar relatório do dia anterior
            gerar_relatorio_excel_assincrono.delay(
                usuario_id=admin.id,
                periodo='diario'
            )
        
        logger.info(f"Relatórios enviados para {len(admins)} administradores")
        
        return {
            'status': 'success',
            'administradores_notificatos': len(admins)
        }
        
    except Exception as exc:
        logger.error(f"Erro ao enviar relatórios: {str(exc)}")
        raise self.retry(exc=exc, countdown=900)


@shared_task
def health_check_tarefas():
    """
    Health check simples para verificar se workers estão ativos.
    Pode ser chamado periodicamente para monitoramento.
    """
    return {
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'worker': 'active'
    }
