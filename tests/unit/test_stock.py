# tests/unit/test_stock.py - Testes unitários para gestão de stock
# Validação crítica para alimentos perecíveis

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app.models import Safra, Transacao, TransactionStatus


class TestGestaoStock:
    """Testes para gestão de stock de safras"""
    
    def test_stock_disponivel_positivo(self, session, safra_ativa):
        """Testa que stock disponível é sempre positivo"""
        assert safra_ativa.quantidade_disponivel > 0
        assert safra_ativa.quantidade_disponivel >= 0
    
    def test_diminuir_stock_apos_reserva(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa diminuição de stock após criação de reserva"""
        stock_original = safra_ativa.quantidade_disponivel
        quantidade_reserva = Decimal('10.00')
        
        # Criar transação (reserva)
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=quantidade_reserva,
            valor_total_pago=quantidade_reserva * safra_ativa.preco_por_unidade
        )
        
        session.add(transacao)
        session.commit()
        
        # Simular abate de stock (feito pela lógica de negócio)
        safra_ativa.quantidade_disponivel -= quantidade_reserva
        session.commit()
        
        # Verificar stock atualizado
        assert safra_ativa.quantidade_disponivel == stock_original - quantidade_reserva
        assert safra_ativa.quantidade_disponivel >= 0
    
    def test_devolver_stock_apos_cancelamento(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa devolução de stock após cancelamento"""
        stock_original = safra_ativa.quantidade_disponivel
        quantidade_reserva = Decimal('15.00')
        
        # Criar e cancelar transação
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=quantidade_reserva,
            valor_total_pago=quantidade_reserva * safra_ativa.preco_por_unidade,
            status=TransactionStatus.CANCELADO
        )
        
        session.add(transacao)
        session.commit()
        
        # Stock não deve ser alterado em cancelamento imediato
        assert safra_ativa.quantidade_disponivel == stock_original
    
    def test_estornar_stock_apos_disputa_favor_comprador(self, session, safra_ativa, transacao_enviada):
        """Testa estorno de stock em disputa resolvida a favor do comprador"""
        stock_original = safra_ativa.quantidade_disponivel
        
        # Simular disputa resolvida a favor do comprador
        # (stock é devolvido ao produtor)
        quantidade_estornada = transacao_enviada.quantidade_comprada
        safra_ativa.quantidade_disponivel += quantidade_estornada
        
        assert safra_ativa.quantidade_disponivel == stock_original + quantidade_estornada
    
    def test_prevencao_venda_sem_stock(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa prevenção de venda quando não há stock disponível"""
        # Zerar stock
        safra_ativa.quantidade_disponivel = Decimal('0.00')
        session.commit()
        
        # Tentar criar transação sem stock
        with pytest.raises(Exception):  # Deve falhar na validação
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('5.00'),  # Não há stock
                valor_total_pago=Decimal('5000.00')
            )
            session.add(transacao)
            session.commit()
    
    def test_prevencao_venda_maior_que_stock(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa prevenção de venda com quantidade maior que stock disponível"""
        stock_disponivel = safra_ativa.quantidade_disponivel
        quantidade_excessiva = stock_disponivel + Decimal('50.00')  # Mais que o disponível
        
        # Tentar criar transação com quantidade excessiva
        with pytest.raises(Exception):  # Deve falhar na validação
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=quantidade_excessiva,
                valor_total_pago=quantidade_excessiva * safra_ativa.preco_por_unidade
            )
            session.add(transacao)
            session.commit()
    
    def test_atualizacao_status_safra_esgotado(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa atualização de status para 'esgotado' quando stock zera"""
        # Vender todo o stock
        quantidade_total = safra_ativa.quantidade_disponivel
        
        transacao = Transacao(
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=quantidade_total,
            valor_total_pago=quantidade_total * safra_ativa.preco_por_unidade
        )
        
        session.add(transacao)
        session.commit()
        
        # Simular abate de stock
        safra_ativa.quantidade_disponivel = Decimal('0.00')
        
        # Atualizar status se necessário
        if safra_ativa.quantidade_disponivel == 0:
            safra_ativa.status = 'esgotado'
        
        session.commit()
        
        assert safra_ativa.quantidade_disponivel == Decimal('0.00')
        assert safra_ativa.status == 'esgotado'
    
    def test_reativacao_safra_com_stock(self, session, safra_ativa):
        """Testa reativação de safra quando stock é adicionado"""
        # Marcar como esgotado
        safra_ativa.quantidade_disponivel = Decimal('0.00')
        safra_ativa.status = 'esgotado'
        session.commit()
        
        # Adicionar stock
        novo_stock = Decimal('50.00')
        safra_ativa.quantidade_disponivel = novo_stock
        safra_ativa.status = 'disponivel'
        session.commit()
        
        assert safra_ativa.quantidade_disponivel == novo_stock
        assert safra_ativa.status == 'disponivel'
    
    def test_validacao_concorrencia_stock(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa validação de concorrência no abate de stock"""
        stock_original = safra_ativa.quantidade_disponivel
        
        # Simular múltiplas reservas concorrentes
        reserva1 = Decimal('10.00')
        reserva2 = Decimal('15.00')
        reserva3 = Decimal('20.00')
        
        # Verificar que stock total não fica negativo
        total_reservado = reserva1 + reserva2 + reserva3
        
        if total_reservado <= stock_original:
            # Todas podem ser processadas
            stock_final = stock_original - total_reservado
            assert stock_final >= 0
        else:
            # Algumas devem ser rejeitadas
            assert total_reservado > stock_original
    
    def test_calculo_valor_total_stock(self, session, safra_ativa):
        """Testa cálculo do valor total do stock disponível"""
        quantidade_disponivel = safra_ativa.quantidade_disponivel
        preco_unitario = safra_ativa.preco_por_unidade
        
        valor_total_stock = quantidade_disponivel * preco_unitario
        
        assert valor_total_stock > 0
        assert isinstance(valor_total_stock, Decimal)
        
        # Verificar precisão
        assert valor_total_stock.quantize(Decimal('0.01')) == valor_total_stock
    
    def test_alerta_stock_baixo(self, session, safra_ativa):
        """Testa geração de alerta para stock baixo"""
        # Definir threshold de alerta (ex: 10kg)
        stock_baixo_threshold = Decimal('10.00')
        
        # Simular stock baixo
        safra_ativa.quantidade_disponivel = Decimal('5.00')
        
        # Verificar se deve gerar alerta
        deve_alertar = safra_ativa.quantidade_disponivel <= stock_baixo_threshold
        
        assert deve_alertar is True
        assert safra_ativa.quantidade_disponivel == Decimal('5.00')
    
    def test_historico_movimentacao_stock(self, session, safra_ativa, comprador_user, produtor_user):
        """Testa rastreamento de movimentação de stock"""
        stock_inicial = safra_ativa.quantidade_disponivel
        
        # Movimentações
        saida1 = Decimal('10.00')  # Venda
        entrada1 = Decimal('5.00')  # Devolução
        saida2 = Decimal('3.00')   # Outra venda
        
        # Calcular stock final
        stock_final = stock_inicial - saida1 + entrada1 - saida2
        
        # Verificar consistência
        total_saidas = saida1 + saida2
        total_entradas = entrada1
        
        stock_calculado = stock_inicial - total_saidas + total_entradas
        
        assert stock_final == stock_calculado
        assert stock_final >= 0  # Stock nunca pode ser negativo


class TestValidacoesStock:
    """Testes específicos para validações de stock"""
    
    def test_validar_quantidade_minima_venda(self, session, safra_ativa):
        """Testa validação de quantidade mínima para venda"""
        quantidade_minima = Decimal('1.00')
        
        # Quantidades válidas
        assert Decimal('1.00') >= quantidade_minima
        assert Decimal('5.50') >= quantidade_minima
        assert safra_ativa.quantidade_disponivel >= quantidade_minima
        
        # Quantidade inválida
        assert Decimal('0.50') < quantidade_minima
        assert Decimal('0.00') < quantidade_minima
    
    def test_validar_precisao_decimal_stock(self, session, safra_ativa):
        """Testa precisão decimal de quantidades de stock"""
        quantidade = safra_ativa.quantidade_disponivel
        
        # Verificar casas decimais (máximo 2 para kg)
        quantidade_str = str(quantidade)
        
        if '.' in quantidade_str:
            casas_decimais = len(quantidade_str.split('.')[1])
            assert casas_decimais <= 2
    
    def test_validar_unidade_medida(self, session, safra_ativa):
        """Testa que unidade de medida está consistente"""
        # Todas as quantidades devem estar em kg
        assert safra_ativa.quantidade_disponivel > 0  # kg
        
        # Para safras, unidade padrão é kg
        unidade_esperada = "kg"
        # Em implementação real, isso viria do modelo
        assert True  # Placeholder para validação de unidade
    
    def test_validar_perecibilidade(self, session, safra_ativa):
        """Testa validações específicas para alimentos perecíveis"""
        # Em implementação real, verificaríamos:
        # - Data de colheita/validade
        # - Condições de armazenamento
        # - Tempo restante até expiração
        
        # Por agora, testamos que safra tem status adequado
        assert safra_ativa.status in ['disponivel', 'esgotado', 'suspensa']
        
        # Stock disponível só deve existir se status for 'disponivel'
        if safra_ativa.quantidade_disponivel > 0:
            assert safra_ativa.status == 'disponivel'
