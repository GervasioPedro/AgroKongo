"""
Serviço de notificações para AgroKongo
"""
from typing import Dict, List
from datetime import datetime
from flask_mail import Message
from core.logger import setup_logger

logger = setup_logger("notificacao")


class NotificacaoService:
    """Serviço de notificações multi-canal"""

    def __init__(self, mail_service):
        self.mail = mail_service
        self.whatsapp_api = os.environ.get('WHATSAPP_API_URL')
        self.whatsapp_token = os.environ.get('WHATSAPP_API_TOKEN')

    def enviar_notificacao_interesse(
            self,
            produtor_id: int,
            comprador_nome: str,
            produto_nome: str,
            quantidade: str,
            preco_max: str
    ) -> Dict:
        """
        Envia notificação de novo interesse para produtor
        """
        try:
            # Preparar mensagem
            mensagem = f"""
            🌾 Novo Interesse Recebido!

            Comprador: {comprador_nome}
            Produto: {produto_nome}
            Quantidade: {quantidade} kg
            Preço Máximo: {preco_max} Kz

            Acesse seu painel para responder.
            """

            # Enviar por múltiplos canais
            resultados = []

            # 1. Email
            email_result = self._enviar_email(
                produtor_id,
                "Novo Interesse Recebido",
                mensagem
            )
            resultados.append(('email', email_result))

            # 2. WhatsApp
            whatsapp_result = self._enviar_whatsapp(
                produtor_id,
                mensagem
            )
            resultados.append(('whatsapp', whatsapp_result))

            # 3. Push Notification (simulado)
            push_result = self._enviar_push(
                produtor_id,
                "Novo Interesse",
                mensagem
            )
            resultados.append(('push', push_result))

            logger.info(f"Notificação interesse enviada: {produtor_id}")

            return {
                'sucesso': True,
                'resultados': resultados
            }

        except Exception as e:
            logger.error(f"Erro ao enviar notificação de interesse: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def enviar_notificacao_status_transacao(
            self,
            usuario_id: int,
            tipo_usuario: str,
            safra_id: int,
            status: str
    ) -> Dict:
        """
        Envia notificação de mudança de status de transação
        """
        try:
            # Mensagem baseada no status
            mensagens = {
                'em_negociacao': {
                    'titulo': 'Negociação Iniciada',
                    'corpo': f'Sua safra #{safra_id} está em negociação.'
                },
                'confirmado': {
                    'titulo': 'Venda Confirmada',
                    'corpo': f'Sua safra #{safra_id} foi confirmada com sucesso!'
                },
                'entregue': {
                    'titulo': 'Produto Entregue',
                    'corpo': f'O produto da safra #{safra_id} foi entregue com sucesso.'
                },
                'cancelado': {
                    'titulo': 'Transação Cancelada',
                    'corpo': f'A transação da safra #{safra_id} foi cancelada.'
                }
            }

            mensagem = mensagens.get(status, {
                'titulo': 'Status Atualizado',
                'corpo': f'O status da safra #{safra_id} foi atualizado para: {status}'
            })

            # Enviar notificação
            resultados = []

            email_result = self._enviar_email(
                usuario_id,
                mensagem['titulo'],
                mensagem['corpo']
            )
            resultados.append(('email', email_result))

            whatsapp_result = self._enviar_whatsapp(
                usuario_id,
                f"{mensagem['titulo']}: {mensagem['corpo']}"
            )
            resultados.append(('whatsapp', whatsapp_result))

            logger.info(f"Notificação status enviada: {usuario_id} - {status}")

            return {
                'sucesso': True,
                'resultados': resultados
            }

        except Exception as e:
            logger.error(f"Erro ao enviar notificação de status: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e)
            }

    def _enviar_email(self, usuario_id: int, assunto: str, corpo: str) -> bool:
        """Envia email de notificação"""
        try:
            from core.database import get_cursor
            cursor = get_cursor()
            cursor.execute("SELECT nome, telemovel FROM usuarios WHERE id = ?", (usuario_id,))
            usuario = cursor.fetchone()

            if not usuario:
                return False

            msg = Message(
                subject=assunto,
                recipients=[f"{usuario['telemovel']}@agrokongo.ao"],  # Simulação
                body=corpo
            )
            self.mail.send(msg)
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            return False

    def _enviar_whatsapp(self, usuario_id: int, mensagem: str) -> bool:
        """Envia mensagem via WhatsApp Business API"""
        try:
            from core.database import get_cursor
            cursor = get_cursor()
            cursor.execute("SELECT telemovel FROM usuarios WHERE id = ?", (usuario_id,))
            usuario = cursor.fetchone()

            if not usuario:
                return False

            # Formatar número para WhatsApp (ex: 244942050656)
            numero_whatsapp = usuario['telemovel']
            if not numero_whatsapp.startswith('244'):
                numero_whatsapp = f"244{numero_whatsapp.lstrip('9')}"

            payload = {
                'messaging_product': 'whatsapp',
                'to': numero_whatsapp,
                'type': 'text',
                'text': {'body': mensagem}
            }

            response = requests.post(
                self.whatsapp_api,
                json=payload,
                headers={
                    'Authorization': f'Bearer {self.whatsapp_token}',
                    'Content-Type': 'application/json'
                }
            )

            return response.status_code == 200

        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
            return False

    def _enviar_push(self, usuario_id: int, titulo: str, corpo: str) -> bool:
        """Envia notificação push (simulado)"""
        # Implementar com Firebase Cloud Messaging ou similar
        # Por enquanto, apenas log
        logger.info(f"Push notification para {usuario_id}: {titulo} - {corpo}")
        return True