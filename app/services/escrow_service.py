"""
Serviço de Escrow - Centraliza toda a lógica de negócio do sistema de custódia
"""
from decimal import Decimal
from datetime import datetime, timezone
from typing import Tuple, Optional
from app.models import Transacao, Usuario, Notificacao, TransactionStatus, HistoricoStatus, LogAuditoria
from app.extensions import db


class EscrowService:
    
    @staticmethod
    def validar_pagamento(transacao_id: int, admin_id: int) -> Tuple[bool, str]:
        """
        Valida pagamento e move para escrow
        
        Args:
            transacao_id: ID da transação
            admin_id: ID do administrador que está validando
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            transacao = Transacao.query.with_for_update().get(transacao_id)
            
            if not transacao:
                return False, "Transação não encontrada"
            
            if transacao.status != TransactionStatus.ANALISE:
                return False, "Transação não está em análise"
            
            # Atualizar status
            status_anterior = transacao.status
            transacao.status = TransactionStatus.ESCROW
            transacao.data_pagamento_escrow = datetime.now(timezone.utc)
            
            # Histórico
            db.session.add(HistoricoStatus(
                transacao_id=transacao.id,
                status_anterior=status_anterior,
                status_novo=TransactionStatus.ESCROW,
                usuario_alteracao=admin_id,
                observacoes="Pagamento validado pelo administrador"
            ))
            
            # Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="VALIDACAO_PAGAMENTO",
                detalhes=f"Ref {transacao.fatura_ref} aprovada e movida para ESCROW"
            ))
            
            # Notificar produtor
            db.session.add(Notificacao(
                usuario_id=transacao.vendedor_id,
                mensagem=f"✅ Pagamento validado! Pode enviar a mercadoria (Ref: {transacao.fatura_ref})",
                link=f"/produtor/dashboard"
            ))
            
            db.session.commit()
            return True, "Pagamento validado com sucesso"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao validar pagamento: {str(e)}"
    
    @staticmethod
    def liberar_pagamento(transacao_id: int, admin_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Libera pagamento para o produtor após confirmação de entrega
        
        Args:
            transacao_id: ID da transação
            admin_id: ID do admin (opcional, pode ser automático)
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            transacao = Transacao.query.with_for_update().get(transacao_id)
            
            if not transacao:
                return False, "Transação não encontrada"
            
            if transacao.status != TransactionStatus.ENTREGUE:
                return False, "Mercadoria ainda não foi entregue"
            
            if transacao.transferencia_concluida:
                return False, "Pagamento já foi liberado"
            
            # Liberar saldo para o vendedor
            vendedor = transacao.vendedor
            vendedor.saldo_disponivel = (vendedor.saldo_disponivel or Decimal('0')) + transacao.valor_liquido_vendedor
            
            # Atualizar transação
            transacao.status = TransactionStatus.FINALIZADO
            transacao.data_liquidacao = datetime.now(timezone.utc)
            transacao.transferencia_concluida = True
            
            # Notificar produtor
            db.session.add(Notificacao(
                usuario_id=vendedor.id,
                mensagem=f"💰 Saldo liberado! Recebeu {transacao.valor_liquido_vendedor} Kz (Ref: {transacao.fatura_ref})",
                link="/produtor/dashboard"
            ))
            
            # Log
            if admin_id:
                db.session.add(LogAuditoria(
                    usuario_id=admin_id,
                    acao="LIBERACAO_PAGAMENTO",
                    detalhes=f"Liberou {transacao.valor_liquido_vendedor} Kz para {vendedor.nome}"
                ))
            
            db.session.commit()
            return True, "Pagamento liberado com sucesso"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao liberar pagamento: {str(e)}"
    
    @staticmethod
    def rejeitar_pagamento(transacao_id: int, admin_id: int, motivo: str) -> Tuple[bool, str]:
        """
        Rejeita um pagamento e retorna ao status pendente
        
        Args:
            transacao_id: ID da transação
            admin_id: ID do administrador
            motivo: Motivo da rejeição
            
        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        try:
            transacao = Transacao.query.with_for_update().get(transacao_id)
            
            if not transacao:
                return False, "Transação não encontrada"
            
            if transacao.status != TransactionStatus.ANALISE:
                return False, "Transação não está em análise"
            
            # Voltar ao status pendente
            status_anterior = transacao.status
            transacao.status = TransactionStatus.AGUARDANDO_PAGAMENTO
            transacao.comprovativo_path = None
            
            # Histórico
            db.session.add(HistoricoStatus(
                transacao_id=transacao.id,
                status_anterior=status_anterior,
                status_novo=TransactionStatus.AGUARDANDO_PAGAMENTO,
                usuario_alteracao=admin_id,
                observacoes=f"Pagamento rejeitado: {motivo}"
            ))
            
            # Log
            db.session.add(LogAuditoria(
                usuario_id=admin_id,
                acao="REJEICAO_PAGAMENTO",
                detalhes=f"Rejeitou pagamento da Ref: {transacao.fatura_ref}. Motivo: {motivo}"
            ))
            
            # Notificar comprador
            db.session.add(Notificacao(
                usuario_id=transacao.comprador_id,
                mensagem=f"❌ Pagamento rejeitado ({transacao.fatura_ref}). Motivo: {motivo}. Envie novamente.",
                link="/comprador/dashboard"
            ))
            
            db.session.commit()
            return True, "Pagamento rejeitado"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erro ao rejeitar pagamento: {str(e)}"
    
    @staticmethod
    def calcular_valores(valor_total: Decimal, taxa_plataforma: Optional[Decimal] = None) -> dict:
        """
        Calcula valores da transação (comissão e valor líquido)
        
        Args:
            valor_total: Valor total da transação
            taxa_plataforma: Taxa da plataforma (default: 5%)
            
        Returns:
            dict: {'comissao': Decimal, 'valor_liquido': Decimal}
        """
        if taxa_plataforma is None:
            taxa_plataforma = Decimal('0.05')  # 5%
        
        comissao = (valor_total * taxa_plataforma).quantize(Decimal('0.01'))
        valor_liquido = valor_total - comissao
        
        return {
            'comissao': comissao,
            'valor_liquido': valor_liquido
        }
