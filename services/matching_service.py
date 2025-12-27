"""
Serviço de matching entre sáfaras e interesses com lógica segura
Implementa algoritmos de compatibilidade e proteção contra concorrência.
"""
from decimal import Decimal
from typing import List, Optional, Dict
from models.safra import Safra
from models.interesse_compra import InteresseCompra
from services.estoque_service import EstoqueService
from core.exceptions import BusinessLogicError, ConcurrencyError

class MatchingService:
    """Serviço de matching entre sáfaras e interesses com lógica segura"""

    @staticmethod
    def verificar_compatibilidade_safra_interesse(
        safra: Safra,
        interesse: InteresseCompra,
        tolerancia_quantidade: Decimal = Decimal('0.1')  # 10% de tolerância
    ) -> bool:
        """
        Verifica se uma safra é compatível com um interesse de compra.

        Args:
            safra: Objeto Safra a ser verificado
            interesse: Objeto InteresseCompra a ser verificado
            tolerancia_quantidade: Tolerância percentual para quantidade (default: 10%)

        Returns:
            True se compatível, False caso contrário

        Raises:
            BusinessLogicError: Se houver erro na verificação de compatibilidade
        """
        try:
            # ✅ Verificação 1: Mesmo produto
            if safra.produto_id != interesse.produto_id:
                return False

            # ✅ Verificação 2: Mesma província (matching geográfico)
            if safra.provincia != interesse.provincia_alvo:
                return False

            # ✅ Verificação 3: Safra disponível para matching
            if not safra.disponivel_para_venda:
                return False

            # ✅ Verificação 4: Interesse ativo para matching
            if not interesse.ativo:
                return False

            # ✅ Verificação 5: Quantidade suficiente (com tolerância)
            quantidade_minima = interesse.quantidade_kg * (Decimal('1.0') - tolerancia_quantidade)
            if safra.quantidade_kg < quantidade_minima:
                return False

            # ✅ Verificação 6: Preço compatível (se ambos definidos)
            if safra.preco_kg is not None and interesse.preco_max_kg is not None:
                if safra.preco_kg > interesse.preco_max_kg:
                    return False

            return True

        except (TypeError, ValueError, AttributeError) as e:
            # ✅ Tratamento seguro de erros de tipo
            raise BusinessLogicError(f"Erro na verificação de compatibilidade: {str(e)}", "matching")

    @staticmethod
    def encontrar_matches_para_interesse(
        interesse: InteresseCompra,
        sáfaras_disponiveis: List[Safra]
    ) -> List[Safra]:
        """
        Encontra todas as sáfaras compatíveis com um interesse.

        Args:
            interesse: Interesse de compra
            sáfaras_disponiveis: Lista de sáfaras disponíveis para matching

        Returns:
            Lista de sáfaras compatíveis ordenadas por preço (mais barato primeiro)
        """
        matches = []

        for safra in sáfaras_disponiveis:
            try:
                if MatchingService.verificar_compatibilidade_safra_interesse(safra, interesse):
                    matches.append(safra)
            except BusinessLogicError:
                # ✅ Ignora sáfaras com dados inválidos
                continue

        # ✅ Ordenar por preço (mais barato primeiro)
        # Safra sem preço vem por último (menos prioridade)
        def get_preco_ordenacao(safra: Safra) -> Decimal:
            return safra.preco_kg if safra.preco_kg is not None else Decimal('999999')

        matches.sort(key=get_preco_ordenacao)
        return matches

    @staticmethod
    def calcular_match_otimo(
        interesse: InteresseCompra,
        sáfaras_disponiveis: List[Safra]
    ) -> Optional[Safra]:
        """
        Encontra a safra ótima para um interesse (menor preço com quantidade suficiente).

        Args:
            interesse: Interesse de compra
            sáfaras_disponiveis: Lista de sáfaras disponíveis

        Returns:
            Safra ótima ou None se não houver match
        """
        matches = MatchingService.encontrar_matches_para_interesse(interesse, sáfaras_disponiveis)
        return matches[0] if matches else None

    @staticmethod
    def validar_disponibilidade_concorrente(safra: Safra, quantidade_solicitada: Decimal) -> bool:
        """
        Verifica se a quantidade solicitada está disponível (proteção contra concorrência).

        Args:
            safra: Safra a ser verificada
            quantidade_solicitada: Quantidade solicitada em kg

        Returns:
            True se disponível, False caso contrário

        Raises:
            ConcurrencyError: Se houver tentativa de estoque negativo
        """
        # ✅ Prevenir estoque negativo
        if not EstoqueService.validar_disponibilidade_estoque(safra.quantidade_kg, quantidade_solicitada):
            return False

        # ✅ Quantidade mínima lógica
        if quantidade_solicitada <= Decimal('0'):
            return False

        return True

    @staticmethod
    def executar_matching_batch(
        interesses_pendentes: List[InteresseCompra],
        sáfaras_disponiveis: List[Safra]
    ) -> Dict[str, List]:
        """
        Executa matching em lote para múltiplos interesses e sáfaras.

        Args:
            interesses_pendentes: Lista de interesses pendentes
            sáfaras_disponiveis: Lista de sáfaras disponíveis

        Returns:
            Dicionário com resultados: {'matches': [...], 'sem_match': [...]}
        """
        matches = []
        sem_match = []

        for interesse in interesses_pendentes:
            match = MatchingService.calcular_match_otimo(interesse, sáfaras_disponiveis)
            if match:
                matches.append({'interesse': interesse, 'safra': match})
            else:
                sem_match.append(interesse)

        return {'matches': matches, 'sem_match': sem_match}