"""
Serviço de Gestão de Pagamentos
Responsável por validação, liquidação e gestão financeira.
"""
from decimal import Decimal
from datetime import datetime, timezone
from typing import Tuple, Optional
from flask import current_app

from app import scheduler
from app.extensions import db
from app.models import Transacao, Notificacao, LogAuditoria, TransactionStatus
from app.utils.status_helper import status_to_value


class PagamentoService:
    """Serviço responsável por gerir todo o ciclo de pagamentos."""
    
    @staticmethod
    def validar_pagamento(transacao_id: int, admin_id: int) -> Tuple[bool, Optional[str]]:
        """
        Valida um pagamento submetido pelo comprador.
        
        Args:
            transacao_id: ID da transação
            admin_id: ID do admin validando
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            venda = Transacao.query.with_for_update().get_or_404(transacao_id)
            
            if venda.status != status_to_value(TransactionStatus.ANALISE):
                return False, "Esta transação já foi processada ou não está em análise."
            
            # Atualizar status para ESCROW
            venda.mudar_status(status_to_value(TransactionStatus.ESCROW), "Pagamento validado pelo Admin")
            
            # Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="VALIDACAO_PAGAMENTO",
                detalhes=f"Ref {venda.fatura_ref} aprovada.",
                ip=None
            ))
            
            # Notificar vendedor
            db.session.add(Notificacao(
                usuario_id=venda.vendedor_id,
                mensagem=f"💰 Pagamento confirmado para {venda.fatura_ref}! Pode enviar a mercadoria.",
                link='/produtor/vendas'
            ))
            
            # Agendar envio de email (se scheduler estiver ativo)
            try:
                if scheduler.running:
                    from app.tasks import enviar_fatura_email
                    scheduler.add_job(
                        id=f'envio_fatura_{venda.id}',
                        func=enviar_fatura_email,
                        args=[venda.id],
                        trigger='date',
                        run_date=None
                    )
            except Exception as e:
                current_app.logger.warning(f"Falha ao agendar email: {e}")
            
            return True, f"Pagamento {venda.fatura_ref} validado!"
            
        except Exception as e:
            current_app.logger.error(f"ERRO_ADMIN_VALIDACAO (ID: {transacao_id}): {e}")
            return False, "Erro técnico ao processar a validação."
    
    @staticmethod
    def confirmar_transferencia(transacao_id: int, admin_id: int) -> Tuple[bool, Optional[str]]:
        """
        Confirma que a transferência bancária foi realizada para o produtor.
        
        Args:
            transacao_id: ID da transação
            admin_id: ID do admin
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            venda = Transacao.query.with_for_update().get_or_404(transacao_id)
            
            # Verificar se está pronta para liquidação
            if not (venda.status == status_to_value(TransactionStatus.ENTREGUE) and not venda.transferencia_concluida):
                return False, "Esta transação não está pronta para liquidação."
            
            # Marcar como transferida e finalizada
            venda.transferencia_concluida = True
            venda.status = status_to_value(TransactionStatus.FINALIZADO)
            venda.data_liquidacao = datetime.now(timezone.utc)
            
            # Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="LIQUIDACAO_PRODUTOR",
                detalhes=f"Ref {venda.fatura_ref} liquidada.",
                ip=None
            ))
            
            # Notificar produtor
            db.session.add(Notificacao(
                usuario_id=venda.vendedor_id,
                mensagem=f"💵 Pagamento enviado para o seu IBAN (Ref: {venda.fatura_ref}).",
                link='/produtor/dashboard'
            ))
            
            return True, "Liquidação concluída com sucesso!"
            
        except Exception as e:
            current_app.logger.error(f"ERRO LIQUIDACAO: {e}")
            return False, "Erro ao processar liquidação."
    
    @staticmethod
    def rejeitar_pagamento(transacao_id: int, admin_id: int, motivo: str) -> Tuple[bool, Optional[str]]:
        """
        Rejeita um pagamento submetido.
        
        Args:
            transacao_id: ID da transação
            admin_id: ID do admin
            motivo: Motivo da rejeição
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            venda = Transacao.query.get_or_404(transacao_id)
            
            # Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="REJEICAO_PAGAMENTO",
                detalhes=f"Rejeitou pagamento da Ref: {venda.fatura_ref}. Motivo: {motivo}",
                ip=None
            ))
            
            # Voltar ao estado de aguardando pagamento
            venda.mudar_status(status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO), f"Pagamento rejeitado: {motivo}")
            venda.comprovativo_path = None
            
            # Notificar comprador
            db.session.add(Notificacao(
                usuario_id=venda.comprador_id,
                mensagem=f"❌ Pagamento Rejeitado ({venda.fatura_ref}). Motivo: {motivo}. Envie novo comprovativo.",
                link='/comprador/dashboard'
            ))
            
            return True, "Pagamento rejeitado e log registado."
            
        except Exception as e:
            current_app.logger.error(f"Erro rejeitar pagamento: {e}")
            return False, "Erro ao rejeitar pagamento."
    
    @staticmethod
    def calcular_comissao(valor_total: Decimal, taxa: Decimal = Decimal('0.05')) -> Tuple[Decimal, Decimal]:
        """
        Calcula comissão da plataforma e valor líquido.
        
        Args:
            valor_total: Valor total da transação
            taxa: Taxa de comissão (padrão 5%)
            
        Returns:
            Tuple[comissao, valor_liquido]
        """
        comissao = (valor_total * taxa).quantize(Decimal('0.01'))
        valor_liquido = (valor_total - comissao).quantize(Decimal('0.01'))
        return comissao, valor_liquido
