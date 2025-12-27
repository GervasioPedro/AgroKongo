"""
Serviço de cálculo de estoque com validações rigorosas
Implementa conversões seguras entre unidades e cálculos com arredondamento controlado.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
from models import UnidadeMedida


class EstoqueService:
    """Serviço de cálculo de estoque com validações rigorosas"""

    # Fatores de conversão padrão (configurável por produto)
    FATORES_CONVERSAO: Dict[str, Decimal] = {
        'kg': Decimal('1.0'),
        'saco': Decimal('50.0'),  # Saco padrão de 50kg para produtos agrícolas
        'tonelada': Decimal('1000.0')
    }

    QUANTIDADES_MINIMAS: Dict[str, Decimal] = {
        'kg': Decimal('1.0'),
        'saco': Decimal('1.0'),
        'tonelada': Decimal('0.1')
    }

    @classmethod
    def converter_para_kg(cls, quantidade: Decimal, unidade: str) -> Decimal:
        """
        Converte quantidade para kg com arredondamento seguro.

        Args:
            quantidade: Quantidade na unidade original
            unidade: Unidade de medida original

        Returns:
            Quantidade convertida para kg

        Raises:
            ValueError: Se unidade não suportada ou quantidade inválida
        """
        if not isinstance(quantidade, Decimal):
            quantidade = Decimal(str(quantidade))

        if unidade not in cls.FATORES_CONVERSAO:
            raise ValueError(f"Unidade não suportada: {unidade}")

        if quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva")

        fator = cls.FATORES_CONVERSAO[unidade]
        quantidade_kg = quantidade * fator

        # Arredondamento seguro para evitar erros de ponto flutuante
        return quantidade_kg.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

    @classmethod
    def converter_de_kg(cls, quantidade_kg: Decimal, unidade: str) -> Decimal:
        """
        Converte kg para unidade original com arredondamento seguro.

        Args:
            quantidade_kg: Quantidade em kg
            unidade: Unidade de medida alvo

        Returns:
            Quantidade convertida para unidade original

        Raises:
            ValueError: Se unidade não suportada ou quantidade inválida
        """
        if not isinstance(quantidade_kg, Decimal):
            quantidade_kg = Decimal(str(quantidade_kg))

        if unidade not in cls.FATORES_CONVERSAO:
            raise ValueError(f"Unidade não suportada: {unidade}")

        if quantidade_kg <= 0:
            raise ValueError("Quantidade em kg deve ser positiva")

        fator = cls.FATORES_CONVERSAO[unidade]
        quantidade = quantidade_kg / fator

        return quantidade.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

    @classmethod
    def validar_quantidade_minima(cls, quantidade: Decimal, unidade: str) -> bool:
        """
        Valida se a quantidade atende ao mínimo para a unidade especificada.

        Args:
            quantidade: Quantidade a ser validada
            unidade: Unidade de medida

        Returns:
            True se quantidade é válida, False caso contrário
        """
        if not isinstance(quantidade, Decimal):
            quantidade = Decimal(str(quantidade))

        quantidade_minima = cls.QUANTIDADES_MINIMAS.get(unidade, Decimal('1.0'))
        return quantidade >= quantidade_minima

    @classmethod
    def calcular_preco_total(cls, preco_kg: Decimal, quantidade_kg: Decimal) -> Decimal:
        """
        Calcula preço total com arredondamento seguro para moeda.

        Args:
            preco_kg: Preço por kg
            quantidade_kg: Quantidade em kg

        Returns:
            Preço total arredondado para 2 casas decimais

        Raises:
            ValueError: Se preços ou quantidades forem inválidos
        """
        if not isinstance(preco_kg, Decimal):
            preco_kg = Decimal(str(preco_kg))
        if not isinstance(quantidade_kg, Decimal):
            quantidade_kg = Decimal(str(quantidade_kg))

        if preco_kg <= 0:
            raise ValueError("Preço por kg deve ser positivo")
        if quantidade_kg <= 0:
            raise ValueError("Quantidade deve ser positiva")

        preco_total = preco_kg * quantidade_kg
        return preco_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def validar_disponibilidade_estoque(cls, quantidade_disponivel: Decimal,
                                        quantidade_solicitada: Decimal) -> bool:
        """
        Valida se a quantidade solicitada está disponível no estoque.

        Args:
            quantidade_disponivel: Quantidade disponível em estoque (kg)
            quantidade_solicitada: Quantidade solicitada (kg)

        Returns:
            True se disponível, False caso contrário
        """
        if not isinstance(quantidade_disponivel, Decimal):
            quantidade_disponivel = Decimal(str(quantidade_disponivel))
        if not isinstance(quantidade_solicitada, Decimal):
            quantidade_solicitada = Decimal(str(quantidade_solicitada))

        # Prevenir estoque negativo
        if quantidade_solicitada <= 0:
            return False

        if quantidade_disponivel <= 0:
            return False

        return quantidade_disponivel >= quantidade_solicitada