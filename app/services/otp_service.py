# app/services/otp_service.py - Sistema OTP completo
# Implementação de geração, envio e validação de códigos OTP

import random
import string
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from app.extensions import db
from flask import current_app
from app.models import Usuario, LogAuditoria


class OTPService:
    """Serviço completo para gestão de códigos OTP"""
    
    # Armazenamento temporário de códigos (em produção, usar Redis)
    _otp_cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def gerar_codigo_otp(cls, length: int = 6) -> str:
        """
        Gera código OTP numérico
        Padrão: 6 dígitos numéricos
        """
        return ''.join(random.choices(string.digits, k=length))
    
    @classmethod
    def gerar_hash_otp(cls, codigo: str, telemovel: str) -> str:
        """
        Gera hash seguro do código OTP para armazenamento
        Evita armazenar código em texto puro
        """
        salt = f"{telemovel}{current_app.config.get('SECRET_KEY', 'default')}"
        return hashlib.sha256(f"{codigo}{salt}".encode()).hexdigest()
    
    @classmethod
    def armazenar_otp(cls, telemovel: str, codigo: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Armazena OTP com metadados para validação
        Retorna dicionário com informações do OTP
        """
        otp_hash = cls.gerar_hash_otp(codigo, telemovel)
        
        otp_data = {
            'hash': otp_hash,
            'codigo': codigo,  # Apenas para desenvolvimento (remover em produção)
            'telemovel': telemovel,
            'data_criacao': datetime.now(timezone.utc),
            'data_expiracao': datetime.now(timezone.utc) + timedelta(minutes=10),  # 10 min validade
            'tentativas': 0,
            'max_tentativas': 3,
            'ip_address': ip_address,
            'validado': False
        }
        
        # Armazenar em cache (em produção, usar Redis)
        cls._otp_cache[telemovel] = otp_data
        
        # Log de auditoria
        db.session.add(LogAuditoria(
            usuario_id=None,  # Sistema
            acao="OTP_GERADO",
            detalhes=f"OTP gerado para telemovel {telemovel[-4:]} IP: {ip_address}",
            ip=ip_address
        ))
        db.session.commit()
        
        return otp_data
    
    @classmethod
    def enviar_otp_sms(cls, telemovel: str, codigo: str) -> bool:
        """
        Envia código OTP via SMS
        Em produção, integrar com API de SMS (ex: Twilio, MessageBird)
        """
        try:
            # Configuração da API (em produção, usar variáveis de ambiente)
            api_url = current_app.config.get('SMS_API_URL')
            api_key = current_app.config.get('SMS_API_KEY')
            
            if not api_url or not api_key:
                current_app.logger.warning("Configuração de SMS não encontrada. Usando modo simulado.")
                return cls._envio_simulado(telemovel, codigo, 'SMS')
            
            # Implementação real com API de SMS
            import requests
            
            payload = {
                'to': f"+244{telemovel}",  # Formato internacional
                'message': f"Seu código AgroKongo é: {codigo}. Validade: 10 minutos.",
                'api_key': api_key
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                current_app.logger.info(f"SMS enviado para {telemovel}")
                return True
            else:
                current_app.logger.error(f"Falha no SMS: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar SMS: {e}")
            return False
    
    @classmethod
    def enviar_otp_whatsapp(cls, telemovel: str, codigo: str) -> bool:
        """
        Envia código OTP via WhatsApp
        Em produção, integrar com API WhatsApp (ex: Twilio WhatsApp, Meta Business API)
        """
        try:
            # Configuração da API
            api_url = current_app.config.get('WHATSAPP_API_URL')
            token = current_app.config.get('WHATSAPP_TOKEN')
            
            if not api_url or not token:
                current_app.logger.warning("Configuração de WhatsApp não encontrada. Usando modo simulado.")
                return cls._envio_simulado(telemovel, codigo, 'WhatsApp')
            
            # Implementação real com API WhatsApp
            import requests
            
            payload = {
                'to': f"244{telemovel}",  # Formato sem +
                'message': f"🌱 *AgroKongo*\n\nSeu código de verificação é: *{codigo}*\n\nValidade: 10 minutos\n\nSe não solicitou, ignore esta mensagem.",
                'token': token
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                current_app.logger.info(f"WhatsApp enviado para {telemovel}")
                return True
            else:
                current_app.logger.error(f"Falha no WhatsApp: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar WhatsApp: {e}")
            return False
    
    @classmethod
    def _envio_simulado(cls, telemovel: str, codigo: str, canal: str) -> bool:
        """
        Modo simulado para desenvolvimento/testes
        Em produção, remover este método
        """
        current_app.logger.info(f"[SIMULAÇÃO] {canal} para {telemovel}: Código {codigo}")
        print(f"\n🌱 AgroKongo - {canal} Simulado")
        print(f"📱 Telemovel: +244 {telemovel}")
        print(f"🔐 Código OTP: {codigo}")
        print(f"⏰ Validade: 10 minutos")
        print(f"📝 Em produção, usar API real de {canal}\n")
        return True
    
    @classmethod
    def validar_otp(cls, telemovel: str, codigo_informado: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Valida código OTP informado
        Retorna dicionário com resultado da validação
        """
        # Obter dados OTP do cache
        otp_data = cls._otp_cache.get(telemovel)
        
        if not otp_data:
            return {
                'valido': False,
                'mensagem': 'Código não encontrado ou expirado. Solicite um novo código.',
                'tentativas_restantes': 0
            }
        
        # Verificar expiração
        if datetime.now(timezone.utc) > otp_data['data_expiracao']:
            cls._limpar_otp(telemovel)
            return {
                'valido': False,
                'mensagem': 'Código expirado. Solicite um novo código.',
                'tentativas_restantes': 0
            }
        
        # Verificar tentativas máximas
        if otp_data['tentativas'] >= otp_data['max_tentativas']:
            cls._limpar_otp(telemovel)
            return {
                'valido': False,
                'mensagem': 'Número máximo de tentativas excedido. Solicite um novo código.',
                'tentativas_restantes': 0
            }
        
        # Incrementar tentativas
        otp_data['tentativas'] += 1
        cls._otp_cache[telemovel] = otp_data
        
        # Verificar hash do código
        codigo_hash = cls.gerar_hash_otp(codigo_informado, telemovel)
        
        if codigo_hash == otp_data['hash']:
            # Código válido
            cls._limpar_otp(telemovel)
            
            # Log de sucesso
            db.session.add(LogAuditoria(
                usuario_id=None,  # Sistema
                acao="OTP_VALIDADO",
                detalhes=f"OTP validado para telemovel {telemovel[-4:]} IP: {ip_address}",
                ip=ip_address
            ))
            db.session.commit()
            
            return {
                'valido': True,
                'mensagem': 'Código validado com sucesso!',
                'tentativas_restantes': 0
            }
        else:
            # Código inválido
            tentativas_restantes = otp_data['max_tentativas'] - otp_data['tentativas']
            
            # Log de falha
            db.session.add(LogAuditoria(
                usuario_id=None,  # Sistema
                acao="OTP_INVALIDO",
                detalhes=f"Tentativa {otp_data['tentativas']} inválida para {telemovel[-4:]} IP: {ip_address}",
                ip=ip_address
            ))
            db.session.commit()
            
            return {
                'valido': False,
                'mensagem': f'Código inválido. Tentativas restantes: {tentativas_restantes}',
                'tentativas_restantes': tentativas_restantes
            }
    
    @classmethod
    def _limpar_otp(cls, telemovel: str):
        """
        Remove OTP do cache após validação ou expiração
        """
        if telemovel in cls._otp_cache:
            del cls._otp_cache[telemovel]
    
    @classmethod
    def limpar_otps_expirados(cls):
        """
        Limpa OTPs expirados do cache (task agendada)
        """
        agora = datetime.now(timezone.utc)
        expirados = []
        
        for telemovel, otp_data in cls._otp_cache.items():
            if agora > otp_data['data_expiracao']:
                expirados.append(telemovel)
        
        for telemovel in expirados:
            cls._limpar_otp(telemovel)
        
        return len(expirados)
    
    @classmethod
    def verificar_usuario_existente(cls, telemovel: str) -> bool:
        """
        Verifica se telemovel já está cadastrado
        Para fluxo alternativo 5B
        """
        return Usuario.query.filter_by(telemovel=telemovel).first() is not None
    
    @classmethod
    def obter_status_otp(cls, telemovel: str) -> Optional[Dict[str, Any]]:
        """
        Obtém status atual do OTP para debugging
        """
        return cls._otp_cache.get(telemovel)


# Funções de conveniência para integração
def gerar_e_enviar_otp(telemovel: str, canal: str = 'whatsapp', ip_address: str = None) -> Dict[str, Any]:
    """
    Gera e envia OTP em uma única chamada
    """
    # Verificar se usuário já existe (fluxo alternativo 5B)
    if OTPService.verificar_usuario_existente(telemovel):
        return {
            'sucesso': False,
            'mensagem': 'Este número já possui uma conta na AgroKongo. Tente recuperar a senha.',
            'codigo': None
        }
    
    # Gerar código
    codigo = OTPService.gerar_codigo_otp()
    
    # Armazenar OTP
    otp_data = OTPService.armazenar_otp(telemovel, codigo, ip_address)
    
    # Enviar código
    if canal.lower() == 'whatsapp':
        enviado = OTPService.enviar_otp_whatsapp(telemovel, codigo)
    else:
        enviado = OTPService.enviar_otp_sms(telemovel, codigo)
    
    if enviado:
        return {
            'sucesso': True,
            'mensagem': f'Código enviado via {canal.capitalize()}. Validade: 10 minutos.',
            'codigo': codigo,  # Apenas para desenvolvimento
            'expiracao': otp_data['data_expiracao'].isoformat(),
            'max_tentativas': otp_data['max_tentativas']
        }
    else:
        return {
            'sucesso': False,
            'mensagem': f'Falha ao enviar código via {canal}. Tente novamente.',
            'codigo': None
        }


def reenviar_otp(telemovel: str, canal: str = 'whatsapp', ip_address: str = None) -> Dict[str, Any]:
    """
    Reenvia OTP para o mesmo telemóvel
    """
    # Limpar OTP anterior se existir
    OTPService._limpar_otp(telemovel)
    
    # Gerar e enviar novo
    return gerar_e_enviar_otp(telemovel, canal, ip_address)
