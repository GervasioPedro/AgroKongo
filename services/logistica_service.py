"""
Serviço de logística para AgroKongo
"""
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from core.logger import setup_logger

logger = setup_logger("logistica")


class LogisticaService:
    """Serviço de logística integrada"""

    def __init__(self):
        self.transportadoras = [
            {'nome': 'TransAgro Angola', 'taxa_base': Decimal('500')},
            {'nome': 'Logística Rural', 'taxa_base': Decimal('450')},
            {'nome': 'Campos & Estradas', 'taxa_base': Decimal('550')}
        ]

    def calcular_frete(
            self,
            origem_provincia: str,
            origem_municipio: str,
            destino_provincia: str,
            destino_municipio: str,
            peso_kg: Decimal
    ) -> Dict:
        """
        Calcula frete com base em distância e peso
        """
        try:
            # Simular cálculo de distância (em km)
            distancia = self._calcular_distancia(
                origem_provincia, origem_municipio,
                destino_provincia, destino_municipio
            )

            # Calcular custos
            custo_base = Decimal('500')  # Kz por km
            custo_peso = peso_kg * Decimal('10')  # Kz por kg
            custo_total = (distancia * custo_base) + custo_peso

            # Selecionar transportadora mais econômica
            transportadora_selecionada = min(
                self.transportadoras,
                key=lambda t: t['taxa_base']
            )

            return {
                'sucesso': True,
                'transportadora': transportadora_selecionada['nome'],
                'distancia_km': distancia,
                'peso_kg': peso_kg,
                'custo_total': custo_total,
                'prazo_entrega_dias': self._calcular_prazo_entrega(distancia),
                'codigo_rastreio': self._gerar_codigo_rastreio()
            }

        except Exception as e:
            logger.error(f"Erro ao calcular frete: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def agendar_coleta(
            self,
            safra_id: int,
            endereco_coleta: str,
            endereco_entrega: str,
            data_preferida: Optional[str] = None
    ) -> Dict:
        """
        Agenda coleta de produto para entrega
        """
        try:
            # Validar disponibilidade
            disponibilidade = self._verificar_disponibilidade_coleta(data_preferida)

            if not disponibilidade['disponivel']:
                return {
                    'sucesso': False,
                    'erro': 'Data não disponível para coleta'
                }

            # Criar ordem de coleta
            ordem_coleta = {
                'safra_id': safra_id,
                'endereco_coleta': endereco_coleta,
                'endereco_entrega': endereco_entrega,
                'data_agendada': data_preferida or self._data_padrao_coleta(),
                'status': 'agendado',
                'codigo_rastreio': self._gerar_codigo_rastreio(),
                'transportadora': 'TransAgro Angola'  # Selecionar automaticamente
            }

            # Salvar no banco de dados
            self._salvar_ordem_coleta(ordem_coleta)

            logger.info(f"Coleta agendada: {ordem_coleta['codigo_rastreio']}")

            return {
                'sucesso': True,
                'codigo_rastreio': ordem_coleta['codigo_rastreio'],
                'data_coleta': ordem_coleta['data_agendada'],
                'transportadora': ordem_coleta['transportadora']
            }

        except Exception as e:
            logger.error(f"Erro ao agendar coleta: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def atualizar_status_entrega(
            self,
            codigo_rastreio: str,
            status: str,
            localizacao: Optional[str] = None
    ) -> Dict:
        """
        Atualiza status de entrega em tempo real
        """
        try:
            # Atualizar no banco de dados
            self._atualizar_status_banco(codigo_rastreio, status, localizacao)

            # Enviar notificação
            self._enviar_notificacao_status(
                codigo_rastreio, status, localizacao
            )

            logger.info(f"Status atualizado: {codigo_rastreio} -> {status}")

            return {
                'sucesso': True,
                'codigo_rastreio': codigo_rastreio,
                'status': status,
                'localizacao': localizacao
            }

        except Exception as e:
            logger.error(f"Erro ao atualizar status: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def _calcular_distancia(
            self,
            origem_provincia: str,
            origem_municipio: str,
            destino_provincia: str,
            destino_municipio: str
    ) -> Decimal:
        """Calcula distância aproximada entre dois pontos"""
        # Simulação baseada em distâncias médias entre províncias
        distancias_media = {
            ('Luanda', 'Luanda'): 0,
            ('Luanda', 'Bengo'): 50,
            ('Luanda', 'Cuanza Norte'): 120,
            ('Luanda', 'Cuanza Sul'): 180,
            ('Benguela', 'Huambo'): 220,
            ('Huambo', 'Bié'): 300,
            # Adicionar mais distâncias conforme necessário
        }

        chave = (origem_provincia, destino_provincia)
        chave_inversa = (destino_provincia, origem_provincia)

        distancia = distancias_media.get(chave) or distancias_media.get(chave_inversa) or 200

        return Decimal(str(distancia))

    def _calcular_prazo_entrega(self, distancia_km: Decimal) -> int:
        """Calcula prazo de entrega baseado na distância"""
        # 1 dia a cada 100km + 1 dia base
        dias = int(distancia_km / Decimal('100')) + 1
        return max(dias, 1)  # Mínimo 1 dia

    def _gerar_codigo_rastreio(self) -> str:
        """Gera código único de rastreio"""
        import uuid
        import time
        timestamp = str(int(time.time()))[-6:]  # Últimos 6 dígitos do timestamp
        unique_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"AGRO{timestamp}{unique_part}"

    def _verificar_disponibilidade_coleta(self, data_preferida: Optional[str]) -> Dict:
        """Verifica disponibilidade de coleta"""
        from datetime import datetime, timedelta

        if data_preferida:
            data = datetime.strptime(data_preferida, '%Y-%m-%d')
            hoje = datetime.now().date()

            if data.date() < hoje:
                return {'disponivel': False, 'motivo': 'Data passada'}

            if data.date() > hoje + timedelta(days=30):
                return {'disponivel': False, 'motivo': 'Data muito distante'}

        return {'disponivel': True}

    def _data_padrao_coleta(self) -> str:
        """Retorna data padrão de coleta (amanhã)"""
        from datetime import datetime, timedelta
        return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    def _salvar_ordem_coleta(self, ordem_coleta: Dict):
        """Salva ordem de coleta no banco de dados"""
        # Implementar persistência no banco
        pass

    def _atualizar_status_banco(self, codigo_rastreio: str, status: str, localizacao: Optional[str]):
        """Atualiza status no banco de dados"""
        # Implementar atualização no banco
        pass

    def _enviar_notificacao_status(self, codigo_rastreio: str, status: str, localizacao: Optional[str]):
        """Envia notificação de atualização de status"""
        # Implementar envio de notificação
        pass