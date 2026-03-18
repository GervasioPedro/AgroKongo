"""
Serviço de Gestão de Compras
Responsável por toda a lógica de negócio relacionada a compras e transações.
"""
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from typing import Tuple, Optional
from flask import current_app

from app.extensions import db
from app.models import (
    Transacao, Safra, Usuario, Notificacao, 
    LogAuditoria, HistoricoStatus, TransactionStatus
)
from app.utils.status_helper import status_to_value


class CompraService:
    """Serviço responsável por gerir todo o ciclo de vida de uma compra."""
    
    @staticmethod
    def iniciar_compra(safra_id: int, comprador_id: int, quantidade: Decimal) -> Tuple[bool, Optional[Transacao], str]:
        """
        Inicia uma nova compra no marketplace.
        
        Args:
            safra_id: ID da safra a ser comprada
            comprador_id: ID do comprador
            quantidade: Quantidade a ser comprada
            
        Returns:
            Tuple[success, transacao, mensagem]
        """
        try:
            # 1. Validações preliminares
            comprador = Usuario.query.get(comprador_id)
            if not comprador:
                return False, None, "Comprador não encontrado."
            
            if comprador.tipo == 'produtor':
                return False, None, "Não pode comprar: Produtores não podem comprar safras."
            
            if not comprador.conta_validada or not comprador.perfil_completo:
                return False, None, "Complete seu perfil para realizar compras."
            
            # 2. Obter safra com lock pessimista
            safra = Safra.query.with_for_update().get(safra_id)
            if not safra:
                return False, None, "Safra não encontrada."
            
            # 3. Validações de stock
            if safra.produtor_id == comprador_id:
                return False, None, "Não pode comprar a sua própria safra."
            
            if quantidade <= 0:
                return False, None, "A quantidade deve ser maior que zero."
            
            if quantidade > safra.quantidade_disponivel:
                return False, None, f"Quantidade indisponível. Máximo: {safra.quantidade_disponivel}kg"
            
            # 4. Cálculos financeiros
            valor_total = (quantidade * safra.preco_por_unidade).quantize(Decimal('0.01'))
            
            # 5. Criar transação
            nova_transacao = Transacao(
                safra_id=safra.id,
                comprador_id=comprador_id,
                vendedor_id=safra.produtor_id,
                quantidade_comprada=quantidade,
                valor_total_pago=valor_total,
                status=status_to_value(TransactionStatus.PENDENTE)
            )
            
            # 6. Abater stock
            safra.quantidade_disponivel -= quantidade
            if safra.quantidade_disponivel <= 0:
                safra.status = 'esgotado'
            
            # Adicionar transação à sessão primeiro
            db.session.add(nova_transacao)
            
            # Fazer flush para gerar o ID da transação
            db.session.flush()
            
            # 7. Registar histórico (agora com ID disponível)
            nova_transacao.mudar_status(status_to_value(TransactionStatus.PENDENTE), "Reserva criada pelo comprador.")
            
            # 8. Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=comprador_id,
                acao="COMPRA_INICIADA",
                detalhes=f"Ref: {nova_transacao.fatura_ref} | Qtd: {quantidade} | Safra: {safra.id}",
                ip=None  # Será preenchido pela rota
            ))
            
            # Commit explícito para persistir alterações
            db.session.commit()
            
            return True, nova_transacao, f"Reserva {nova_transacao.fatura_ref} efetuada!"
            
        except InvalidOperation as e:
            current_app.logger.error(f"Erro de conversão numérica: {str(e)}")
            return False, None, "Valores numéricos inválidos."
        except Exception as e:
            current_app.logger.error(f"Erro ao iniciar compra: {str(e)}")
            return False, None, "Erro técnico ao processar a encomenda."
    
    @staticmethod
    def aceitar_reserva(transacao_id: int, produtor_id: int) -> Tuple[bool, Optional[str]]:
        """
        Aceita uma reserva pendente.
        
        Args:
            transacao_id: ID da transação
            produtor_id: ID do produtor
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            venda = Transacao.query.with_for_update().get(transacao_id)
            
            if not venda:
                return False, "Transação não encontrada."
            
            if venda.vendedor_id != produtor_id:
                return False, "Esta transação não pertence ao produtor."
            
            if venda.status != status_to_value(TransactionStatus.PENDENTE):
                return False, "Esta reserva já não está pendente."
            
            # Atualizar status
            venda.mudar_status(status_to_value(TransactionStatus.AGUARDANDO_PAGAMENTO), "Aceite pelo produtor")
            
            # Notificar comprador
            db.session.add(Notificacao(
                usuario_id=venda.comprador_id,
                mensagem=f"✅ Pedido {venda.fatura_ref} aceite! Pode proceder ao pagamento.",
                link='/comprador/dashboard'
            ))
            
            # Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=produtor_id,
                acao="VENDA_ACEITE",
                detalhes=f"Ref: {venda.fatura_ref}",
                ip=None
            ))
            
            # Commit explícito para persistir alterações
            db.session.commit()
            
            return True, "Pedido aceite! O comprador foi notificado para pagar."
            
        except Exception as e:
            current_app.logger.error(f"Erro ao aceitar reserva: {str(e)}")
            return False, "Erro técnico ao processar aceitação."
    
    @staticmethod
    def recusar_reserva(transacao_id: int, produtor_id: int) -> Tuple[bool, Optional[str]]:
        """
        Recusa uma reserva pendente.
        
        Args:
            transacao_id: ID da transação
            produtor_id: ID do produtor
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            venda = Transacao.query.with_for_update().get(transacao_id)
            
            if not venda:
                return False, "Transação não encontrada."
            
            if venda.vendedor_id != produtor_id:
                return False, "Esta transação não pertence ao produtor."
            
            if venda.status != status_to_value(TransactionStatus.PENDENTE):
                return False, "Só é possível recusar reservas pendentes."
            
            # Devolver stock
            if venda.safra:
                venda.safra.quantidade_disponivel += venda.quantidade_comprada
            else:
                # Carregar safra se não estiver disponível
                from app.models import Safra
                safra = Safra.query.get(venda.safra_id)
                if safra:
                    safra.quantidade_disponivel += venda.quantidade_comprada
            
            # Atualizar status
            venda.mudar_status(status_to_value(TransactionStatus.CANCELADO), "Recusada pelo produtor")
            
            # Notificar comprador
            db.session.add(Notificacao(
                usuario_id=venda.comprador_id,
                mensagem=f"❌ O seu pedido {venda.fatura_ref} foi recusado pelo produtor.",
                link='/comprador/dashboard'
            ))
            
            # Commit explícito para persistir alterações
            db.session.commit()
            
            return True, "Reserva recusada e stock reposto."
            
        except Exception as e:
            current_app.logger.error(f"Erro ao recusar reserva: {str(e)}")
            db.session.rollback()
            return False, "Erro técnico ao cancelar reserva."
    
    @staticmethod
    def confirmar_envio(transacao_id: int, vendedor_id: int) -> Tuple[bool, Optional[str]]:
        """
        Confirma o envio da mercadoria.
        
        Args:
            transacao_id: ID da transação
            vendedor_id: ID do vendedor
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            transacao = Transacao.query.with_for_update().get_or_404(transacao_id)
            
            if transacao.vendedor_id != vendedor_id:
                return False, "Apenas o vendedor pode confirmar o envio."
            
            if transacao.status != status_to_value(TransactionStatus.ESCROW):
                return False, "O pagamento deve ser confirmado primeiro."
            
            # Atualizar status
            transacao.mudar_status(status_to_value(TransactionStatus.ENVIADO), "Mercadoria enviada pelo produtor.")
            transacao.data_envio = datetime.now(timezone.utc)
            
            # Calcular previsão de entrega
            transacao.calcular_janela_logistica()
            
            # Notificar comprador
            previsao_str = transacao.previsao_entrega.strftime('%d/%m') if transacao.previsao_entrega else "Brevemente"
            db.session.add(Notificacao(
                usuario_id=transacao.comprador_id,
                mensagem=f"🚚 Encomenda {transacao.fatura_ref} enviada! Previsão: {previsao_str}",
                link='/comprador/dashboard'
            ))
            
            # Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=vendedor_id,
                acao="VENDA_ENVIADA",
                detalhes=f"Ref: {transacao.fatura_ref}",
                ip=None
            ))
            
            # Commit explícito para persistir alterações
            db.session.commit()
            
            return True, f"Envio da fatura {transacao.fatura_ref} confirmado!"
            
        except Exception as e:
            current_app.logger.error(f"ERRO_ENVIO_SAFRA (ID: {transacao_id}): {str(e)}")
            return False, "Erro interno ao processar o envio."
    
    @staticmethod
    def confirmar_recebimento(transacao_id: int, comprador_id: int) -> Tuple[bool, Optional[str]]:
        """
        Confirma o recebimento da mercadoria e liberta o pagamento.
        
        Args:
            transacao_id: ID da transação
            comprador_id: ID do comprador
            
        Returns:
            Tuple[success, mensagem]
        """
        try:
            transacao = Transacao.query.with_for_update().get_or_404(transacao_id)
            
            if transacao.comprador_id != comprador_id:
                return False, "Apenas o comprador pode confirmar o recebimento."
            
            if transacao.status != status_to_value(TransactionStatus.ENVIADO):
                return False, "Esta encomenda não está em estado de receção."
            
            # Atualizar status
            transacao.mudar_status(status_to_value(TransactionStatus.FINALIZADO), "Entrega confirmada pelo comprador")
            transacao.data_entrega = datetime.now(timezone.utc)
            transacao.data_liquidacao = datetime.now(timezone.utc)
            
            # Libertar valor líquido ao vendedor
            vendedor = transacao.vendedor
            valor_liquido = Decimal(str(transacao.valor_liquido_vendedor))
            vendedor.saldo_disponivel = (vendedor.saldo_disponivel or Decimal('0.00')) + valor_liquido
            vendedor.vendas_concluidas = (vendedor.vendas_concluidas or 0) + 1
            
            # Notificar vendedor
            db.session.add(Notificacao(
                usuario_id=vendedor.id,
                mensagem=f"💰 Saldo libertado! Recebeste o pagamento da fatura {transacao.fatura_ref}.",
                link='/produtor/vendas'
            ))
            
            # Log de auditoria
            db.session.add(LogAuditoria(
                usuario_id=comprador_id,
                acao="VENDA_FINALIZADA",
                detalhes=f"Ref: {transacao.fatura_ref} | Valor Libertado: {valor_liquido}",
                ip=None
            ))
            
            # Commit explícito para persistir alterações
            db.session.commit()
            
            return True, "Recebimento confirmado! O saldo foi libertado para o produtor."
            
        except Exception as e:
            current_app.logger.error(f"ERRO_RECEBIMENTO: {str(e)}")
            return False, "Erro ao processar a confirmação."
