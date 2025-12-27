"""
Testes para o EstoqueService
Verifica conversões, validações e cálculos com edge cases.
"""
import pytest
from decimal import Decimal
from services.estoque_service import EstoqueService
from models.safra import UnidadeMedida


class TestEstoqueService:
    """Testes para o serviço de estoque"""

    def test_conversao_kg_para_kg(self):
        """Teste de conversão kg para kg"""
        resultado = EstoqueService.converter_para_kg(Decimal('100'), 'kg')
        assert resultado == Decimal('100.000')

    def test_conversao_saco_para_kg(self):
        """Teste de conversão saco para kg (50kg por saco)"""
        resultado = EstoqueService.converter_para_kg(Decimal('2'), 'saco')
        assert resultado == Decimal('100.000')

    def test_conversao_tonelada_para_kg(self):
        """Teste de conversão tonelada para kg (1000kg por tonelada)"""
        resultado = EstoqueService.converter_para_kg(Decimal('1.5'), 'tonelada')
        assert resultado == Decimal('1500.000')

    def test_conversao_invalida(self):
        """Teste de conversão com unidade inválida"""
        with pytest.raises(ValueError, match="Unidade não suportada"):
            EstoqueService.converter_para_kg(Decimal('100'), 'arroba')

    def test_quantidade_negativa(self):
        """Teste de conversão com quantidade negativa"""
        with pytest.raises(ValueError, match="Quantidade deve ser positiva"):
            EstoqueService.converter_para_kg(Decimal('-10'), 'kg')

    def test_quantidade_minima_valida(self):
        """Teste de validação de quantidade mínima"""
        assert EstoqueService.validar_quantidade_minima(Decimal('1'), 'kg') == True
        assert EstoqueService.validar_quantidade_minima(Decimal('1'), 'saco') == True
        assert EstoqueService.validar_quantidade_minima(Decimal('0.1'), 'tonelada') == True

    def test_quantidade_minima_invalida(self):
        """Teste de validação de quantidade mínima inválida"""
        assert EstoqueService.validar_quantidade_minima(Decimal('0.5'), 'tonelada') == False
        assert EstoqueService.validar_quantidade_minima(Decimal('0'), 'kg') == False

    def test_calculo_preco_total(self):
        """Teste de cálculo de preço total com arredondamento"""
        preco_total = EstoqueService.calcular_preco_total(Decimal('50.5'), Decimal('2.3'))
        assert preco_total == Decimal('116.15')  # 50.5 * 2.3 = 116.15

    def test_calculo_preco_total_arredondamento(self):
        """Teste de arredondamento em cálculo de preço total"""
        preco_total = EstoqueService.calcular_preco_total(Decimal('1.0001'), Decimal('3'))
        assert preco_total == Decimal('3.00')  # Deve arredondar para 2 casas

    def test_validacao_disponibilidade_estoque_suficiente(self):
        """Teste de validação de estoque suficiente"""
        assert EstoqueService.validar_disponibilidade_estoque(Decimal('100'), Decimal('80')) == True

    def test_validacao_disponibilidade_estoque_insuficiente(self):
        """Teste de validação de estoque insuficiente"""
        assert EstoqueService.validar_disponibilidade_estoque(Decimal('50'), Decimal('60')) == False

    def test_validacao_disponibilidade_quantidade_zero(self):
        """Teste de validação com quantidade zero"""
        assert EstoqueService.validar_disponibilidade_estoque(Decimal('100'), Decimal('0')) == False

    def test_validacao_disponibilidade_estoque_negativo(self):
        """Teste de validação com estoque negativo"""
        assert EstoqueService.validar_disponibilidade_estoque(Decimal('-10'), Decimal('5')) == False