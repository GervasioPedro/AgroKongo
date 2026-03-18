from decimal import Decimal, ROUND_HALF_UP
from app.extensions import db
from app.models import Safra, Transacao, TransactionStatus, Usuario
from sqlalchemy.exc import SQLAlchemyError

class TransactionService:
    @staticmethod
    def criar_reserva(safra_id, comprador_id, quantidade_kg):
        """
        Cria uma reserva de compra de forma atómica e segura (ACID).
        Retorna: (sucesso: bool, resultado: Transacao ou mensagem_erro: str)
        """
        try:
            # Iniciar transação de base de dados
            # O 'nested' permite rollback parcial se estivermos dentro de outra transação,
            # mas aqui queremos garantir o bloco principal.
            with db.session.begin_nested():
                
                # 1. Pessimistic Locking: Bloqueia a linha da Safra para evitar race conditions
                # (dois users comprarem o último kg ao mesmo tempo)
                safra = Safra.query.with_for_update().get(safra_id)

                if not safra:
                    return False, "Safra não encontrada."

                # 2. Validações de Negócio
                if safra.produtor_id == comprador_id:
                    return False, "Não pode comprar a sua própria safra (Self-dealing)."
                
                if safra.status != 'disponivel':
                    return False, f"Safra indisponível (Status: {safra.status})."

                qtd = Decimal(str(quantidade_kg))
                if qtd <= 0:
                    return False, "Quantidade deve ser maior que zero."
                
                if qtd > safra.quantidade_disponivel:
                    return False, f"Stock insuficiente. Disponível: {safra.quantidade_disponivel}kg"

                # 3. Cálculos Financeiros (Precision Critical)
                preco_unit = safra.preco_por_unidade
                valor_total = (qtd * preco_unit).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Taxa de 5% da Plataforma
                taxa = (valor_total * Decimal('0.05')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                liquido_vendedor = valor_total - taxa

                # 4. Criar Transação
                nova_transacao = Transacao(
                    safra_id=safra.id,
                    comprador_id=comprador_id,
                    vendedor_id=safra.produtor_id,
                    quantidade_comprada=qtd,
                    valor_total_pago=valor_total,
                    comissao_plataforma=taxa,
                    valor_liquido_vendedor=liquido_vendedor,
                    status=TransactionStatus.PENDENTE
                )
                
                db.session.add(nova_transacao)
                
                # 5. Abater Stock
                safra.quantidade_disponivel -= qtd
                if safra.quantidade_disponivel <= 0:
                    safra.status = 'esgotado'
                
                db.session.add(safra)
                
                # O commit acontece automaticamente ao sair do bloco 'with' se não houver erro
                
            # Confirmação final na DB
            db.session.commit()
            return True, nova_transacao

        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erro de base de dados: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Erro inesperado: {str(e)}"
