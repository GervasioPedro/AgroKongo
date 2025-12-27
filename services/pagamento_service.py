"""
Serviço de pagamento para AgroKongo - INTEGRAÇÃO REAL
"""
from decimal import Decimal
from typing import Dict, Optional
import requests
import hashlib
import hmac
from core.logger import setup_logger

logger = setup_logger("pagamento")

class PagamentoService:
    """Serviço de pagamento integrado com sistemas angolanos"""

    def __init__(self):
        self.mpesa_endpoint = "https://api.mpesa.ao/v1/payment"
        self.bai_endpoint = "https://api.bai.ao/v1/transfer"
        self.api_key = os.environ.get('PAGAMENTO_API_KEY')
        self.secret = os.environ.get('PAGAMENTO_SECRET')

    def criar_pedido_pagamento(
        self,
        valor: Decimal,
        comprador_id: int,
        produtor_id: int,
        descricao: str,
        metodo: str = 'mpesa'
    ) -> Dict:
        """
        Cria um pedido de pagamento seguro
        """
        try:
            # Validar valores
            if valor <= 0:
                raise ValueError("Valor deve ser positivo")

            # Criar payload seguro
            payload = {
                'valor': str(valor),
                'comprador_id': comprador_id,
                'produtor_id': produtor_id,
                'descricao': descricao,
                'referencia': self._gerar_referencia_segura(),
                'metodo': metodo,
                'timestamp': self._get_timestamp()
            }

            # Assinar payload
            signature = self._assinar_payload(payload)
            payload['signature'] = signature

            # Enviar para gateway de pagamento
            response = self._enviar_para_gateway(payload, metodo)

            if response.get('sucesso'):
                logger.info(f"Pagamento criado: {response['referencia']}")
                return {
                    'sucesso': True,
                    'referencia': response['referencia'],
                    'qr_code': response.get('qr_code'),
                    'codigo_pagamento': response.get('codigo_pagamento')
                }
            else:
                raise Exception(f"Erro no gateway: {response.get('mensagem')}")

        except Exception as e:
            logger.error(f"Erro ao criar pedido de pagamento: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def verificar_pagamento(self, referencia: str) -> Dict:
        """
        Verifica status de pagamento
        """
        try:
            payload = {
                'referencia': referencia,
                'timestamp': self._get_timestamp()
            }

            signature = self._assinar_payload(payload)
            payload['signature'] = signature

            response = requests.get(
                f"{self.mpesa_endpoint}/status",
                params=payload,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )

            return response.json()

        except Exception as e:
            logger.error(f"Erro ao verificar pagamento: {str(e)}")
            return {'sucesso': False, 'erro': str(e)}

    def _gerar_referencia_segura(self) -> str:
        """Gera referência única e segura para transação"""
        import uuid
        import time
        timestamp = str(int(time.time()))
        unique_id = str(uuid.uuid4()).replace('-', '')[:8]
        return f"AGROKONGO_{timestamp}_{unique_id}"

    def _assinar_payload(self, payload: Dict) -> str:
        """Assina payload com HMAC para segurança"""
        message = '&'.join([f"{k}={v}" for k, v in sorted(payload.items())])
        return hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    def _get_timestamp(self) -> str:
        """Obtém timestamp atual"""
        import time
        return str(int(time.time()))

    def _enviar_para_gateway(self, payload: Dict, metodo: str) -> Dict:
        """Envia dados para gateway de pagamento específico"""
        if metodo == 'mpesa':
            response = requests.post(
                self.mpesa_endpoint,
                json=payload,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
        else:
            # Outros métodos de pagamento
            response = requests.post(
                self.bai_endpoint,
                json=payload,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )

        return response.json()