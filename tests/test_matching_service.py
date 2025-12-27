"""
Testes para o MatchingService
Verifica lógica de compatibilidade e proteção contra concorrência.
"""
import pytest
from decimal import Decimal
from models.safra import Safra
from models.interesse_compra import InteresseCompra
from services.matching_service import MatchingService
from core.exceptions import BusinessLogicError


class TestMatchingService:
    """Testes para o serviço de matching"""

    def create_test_safra(self, **kwargs):
        """Cria uma safra de teste com valores padrão"""
        default_safra = {
            'produtor_id': 1,
            'produto_id': 1,
            'quantidade_kg': Decimal('100'),
            'quantidade_original': Decimal('2'),
            'unidade_original': 'saco',
            'preco_kg': Decimal('50'),
            'preco_original': Decimal('2500'),
            'provincia': 'Luanda',
            'municipio': 'Belas'
        }
        default_safra.update(kwargs)
        return Safra(**default_safra)

    def create_test_interesse(self, **kwargs):
        """Cria um interesse de teste com valores padrão"""
        default_interesse = {
            'comprador_id': 2,
            'produto_id': 1,
            'quantidade_kg': Decimal('80'),
            'preco_max_kg': Decimal('60'),
            'provincia_alvo': 'Luanda'
        }
        default_interesse.update(kwargs)
        return InteresseCompra(**default_interesse)

    def test_match_basico_compativel(self):
        """Teste básico de matching compatível"""
        safra = self.create_test_safra()
        interesse = self.create_test_interesse()

        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == True

    def test_match_produto_diferente(self):
        """Teste de matching com produto diferente"""
        safra = self.create_test_safra(produto_id=1)
        interesse = self.create_test_interesse(produto_id=2)

        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == False

    def test_match_provincia_diferente(self):
        """Teste de matching com província diferente"""
        safra = self.create_test_safra(provincia='Luanda')
        interesse = self.create_test_interesse(provincia_alvo='Benguela')

        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == False

    def test_match_quantidade_insuficiente(self):
        """Teste de matching com quantidade insuficiente"""
        safra = self.create_test_safra(quantidade_kg=Decimal('50'))
        interesse = self.create_test_interesse(quantidade_kg=Decimal('80'))

        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == False

    def test_match_quantidade_com_tolerancia(self):
        """Teste de matching com quantidade dentro da tolerância (10%)"""
        safra = self.create_test_safra(quantidade_kg=Decimal('75'))  # 75kg = 93.75% de 80kg
        interesse = self.create_test_interesse(quantidade_kg=Decimal('80'))

        # 75kg >= 80kg * (1 - 0.1) = 72kg → Deve ser compatível
        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == True

    def test_match_preco_incompativel(self):
        """Teste de matching com preço incompatível"""
        safra = self.create_test_safra(preco_kg=Decimal('70'))
        interesse = self.create_test_interesse(preco_max_kg=Decimal('60'))

        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == False

    def test_match_preco_sem_preco_safra(self):
        """Teste de matching quando safra não tem preço definido"""
        safra = self.create_test_safra(preco_kg=None)
        interesse = self.create_test_interesse(preco_max_kg=Decimal('60'))

        # Sem preço na safra, deve ser compatível (preço negociado depois)
        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == True

    def test_match_preco_sem_preco_interesse(self):
        """Teste de matching quando interesse não tem preço máximo"""
        safra = self.create_test_safra(preco_kg=Decimal('50'))
        interesse = self.create_test_interesse(preco_max_kg=None)

        # Sem preço máximo no interesse, deve ser compatível
        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == True

    def test_safra_nao_disponivel(self):
        """Teste de matching com safra não disponível"""
        safra = self.create_test_safra(status='em_negociacao')
        interesse = self.create_test_interesse()

        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == False

    def test_interesse_nao_ativo(self):
        """Teste de matching com interesse não ativo"""
        safra = self.create_test_safra()
        interesse = self.create_test_interesse(status='matched')

        assert MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse) == False

    def test_encontrar_matches_ordenados_por_preco(self):
        """Teste de encontrar matches ordenados por preço"""
        interesse = self.create_test_interesse()

        safra_barata = self.create_test_safra(preco_kg=Decimal('40'))
        safra_media = self.create_test_safra(preco_kg=Decimal('50'))
        safra_cara = self.create_test_safra(preco_kg=Decimal('60'))
        safra_sem_preco = self.create_test_safra(preco_kg=None)

        sáfaras = [safra_cara, safra_sem_preco, safra_barata, safra_media]
        matches = MatchingService.encontrar_matches_para_interesse(interesse, sáfaras)

        # Deve retornar ordenado por preço: barata, media, cara, sem_preco
        assert len(matches) == 4
        assert matches[0].preco_kg == Decimal('40')
        assert matches[1].preco_kg == Decimal('50')
        assert matches[2].preco_kg == Decimal('60')
        assert matches[3].preco_kg is None

    def test_validacao_concorrencia_quantidade_disponivel(self):
        """Teste de validação de concorrência com quantidade disponível"""
        safra = self.create_test_safra(quantidade_kg=Decimal('100'))

        assert MatchingService.validar_disponibilidade_concorrente(safra, Decimal('80')) == True

    def test_validacao_concorrencia_quantidade_excedente(self):
        """Teste de validação de concorrência com quantidade excedente"""
        safra = self.create_test_safra(quantidade_kg=Decimal('50'))

        assert MatchingService.validar_disponibilidade_concorrente(safra, Decimal('60')) == False

    def test_validacao_concorrencia_quantidade_zero(self):
        """Teste de validação de concorrência com quantidade zero"""
        safra = self.create_test_safra(quantidade_kg=Decimal('100'))

        assert MatchingService.validar_disponibilidade_concorrente(safra, Decimal('0')) == False

    def test_validacao_concorrencia_quantidade_negativa(self):
        """Teste de validação de concorrência com quantidade negativa"""
        safra = self.create_test_safra(quantidade_kg=Decimal('100'))

        assert MatchingService.validar_disponibilidade_concorrente(safra, Decimal('-10')) == False