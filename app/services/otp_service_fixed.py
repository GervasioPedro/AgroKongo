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
    _otp_cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def gerar_codigo_otp(cls, length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))
    
    @classmethod
    def gerar_hash_otp(cls, codigo: str, telemovel: str) -> str:
        salt = f"{telemovel}{current_app.config.get('SECRET_KEY', 'default')}"
        return hashlib.sha256(f"{codigo}{salt}".encode()).hexdigest()
    
    @classmethod
    def armazenar_otp(cls, telemovel: str, codigo: str, ip_address: str = None) -> Dict[str, Any]:
        otp_hash = cls.gerar_hash_otp(codigo, telemovel)
        
        otp_data = {
            'hash': otp_hash,
            'codigo': codigo,
            'telemovel': telemovel,
            'data_criacao': datetime.now(timezone.utc),
            'data_expiracao': datetime.now(timezone.utc) + timedelta(minutes=10),
            'tentativas': 0,
            'max_tentativas': 3,
            'ip_address': ip_address,
            'validado': False
        }
        
        cls._otp_cache[telemovel] = otp_data
        
        try:
            db.session.add(LogAuditoria(
                usuario_id=None,
                acao="OTP_GERADO",
                detalhes=f"OTP gerado para telemovel {telemovel[-4:]} IP: {ip_address}",
                ip_address=ip_address
            ))
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Erro ao registrar log OTP: {e}")
        
        return otp_data
    
    @classmethod
    def enviar_otp_sms(cls, telemovel: str, codigo: str) -> bool:
        try:
            api_url = current_app.config.get('SMS_API_URL')
            api_key = current_app.config.get('SMS_API_KEY')
            
            if not api_url or not api_key:
                current_app.logger.info("SMS em modo simulado")
                return cls._envio_simulado(telemovel, codigo, 'SMS')
            
            import requests
            
            payload = {
                'to': f"+244{telemovel}",
                'message': f"Seu codigo AgroKongo e: {codigo}. Validade: 10 minutos.",
                'api_key': api_key
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                current_app.logger.info(f"SMS enviado para {telemovel}")
                return True
            else:
                current_app.logger.error(f"Falha SMS: {response.status_code}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Erro SMS: {e}")
            return False
    
    @classmethod
    def enviar_otp_whatsapp(cls, telemovel: str, codigo: str) -> bool:
        try:
            api_url = current_app.config.get('WHATSAPP_API_URL')
            token = current_app.config.get('WHATSAPP_TOKEN')
            
            if not api_url or not token:
                current_app.logger.info("WhatsApp em modo simulado")
                return cls._envio_simulado(telemovel, codigo, 'WhatsApp')
            
            import requests
            
            payload = {
                'to': f"244{telemovel}",
                'message': f"AgroKongo\n\nSeu codigo de verificacao e: {codigo}\n\nValidade: 10 minutos",
                'token': token
            }
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                current_app.logger.info(f"WhatsApp enviado para {telemovel}")
                return True
            else:
                current_app.logger.error(f"Falha WhatsApp: {response.status_code}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Erro WhatsApp: {e}")
            return False
    
    @classmethod
    def _envio_simulado(cls, telemovel: str, codigo: str, canal: str) -> bool:
        current_app.logger.info(f"[SIMULACAO] {canal} para {telemovel}: Codigo {codigo}")
        print(f"\nAgroKongo - {canal} Simulado")
        print(f"Telemovel: +244 {telemovel}")
        print(f"Codigo OTP: {codigo}")
        print(f"Validade: 10 minutos\n")
        return True
    
    @classmethod
    def validar_otp(cls, telemovel: str, codigo_informado: str, ip_address: str = None) -> Dict[str, Any]:
        otp_data = cls._otp_cache.get(telemovel)
        
        if not otp_data:
            return {
                'valido': False,
                'mensagem': 'Codigo nao encontrado ou expirado. Solicite um novo codigo.',
                'tentativas_restantes': 0
            }
        
        if datetime.now(timezone.utc) > otp_data['data_expiracao']:
            cls._limpar_otp(telemovel)
            return {
                'valido': False,
                'mensagem': 'Codigo expirado. Solicite um novo codigo.',
                'tentativas_restantes': 0
            }
        
        if otp_data['tentativas'] >= otp_data['max_tentativas']:
            cls._limpar_otp(telemovel)
            return {
                'valido': False,
                'mensagem': 'Numero maximo de tentativas excedido. Solicite um novo codigo.',
                'tentativas_restantes': 0
            }
        
        otp_data['tentativas'] += 1
        cls._otp_cache[telemovel] = otp_data
        
        codigo_hash = cls.gerar_hash_otp(codigo_informado, telemovel)
        
        if codigo_hash == otp_data['hash']:
            cls._limpar_otp(telemovel)
            
            try:
                db.session.add(LogAuditoria(
                    usuario_id=None,
                    acao="OTP_VALIDADO",
                    detalhes=f"OTP validado para telemovel {telemovel[-4:]} IP: {ip_address}",
                    ip_address=ip_address
                ))
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Erro ao registrar validacao OTP: {e}")
            
            return {
                'valido': True,
                'mensagem': 'Codigo validado com sucesso!',
                'tentativas_restantes': 0
            }
        else:
            tentativas_restantes = otp_data['max_tentativas'] - otp_data['tentativas']
            
            try:
                db.session.add(LogAuditoria(
                    usuario_id=None,
                    acao="OTP_INVALIDO",
                    detalhes=f"Tentativa {otp_data['tentativas']} invalida para {telemovel[-4:]} IP: {ip_address}",
                    ip_address=ip_address
                ))
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Erro ao registrar tentativa invalida: {e}")
            
            return {
                'valido': False,
                'mensagem': f'Codigo invalido. Tentativas restantes: {tentativas_restantes}',
                'tentativas_restantes': tentativas_restantes
            }
    
    @classmethod
    def _limpar_otp(cls, telemovel: str):
        if telemovel in cls._otp_cache:
            del cls._otp_cache[telemovel]
    
    @classmethod
    def limpar_otps_expirados(cls):
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
        return Usuario.query.filter_by(telemovel=telemovel).first() is not None
    
    @classmethod
    def obter_status_otp(cls, telemovel: str) -> Optional[Dict[str, Any]]:
        return cls._otp_cache.get(telemovel)


def gerar_e_enviar_otp(telemovel: str, canal: str = 'whatsapp', ip_address: str = None) -> Dict[str, Any]:
    if OTPService.verificar_usuario_existente(telemovel):
        return {
            'sucesso': False,
            'mensagem': 'Este numero ja possui uma conta na AgroKongo. Tente recuperar a senha.',
            'codigo': None
        }
    
    codigo = OTPService.gerar_codigo_otp()
    otp_data = OTPService.armazenar_otp(telemovel, codigo, ip_address)
    
    if canal.lower() == 'whatsapp':
        enviado = OTPService.enviar_otp_whatsapp(telemovel, codigo)
    else:
        enviado = OTPService.enviar_otp_sms(telemovel, codigo)
    
    if enviado:
        return {
            'sucesso': True,
            'mensagem': f'Codigo enviado via {canal.capitalize()}. Validade: 10 minutos.',
            'codigo': codigo,
            'expiracao': otp_data['data_expiracao'].isoformat(),
            'max_tentativas': otp_data['max_tentativas']
        }
    else:
        return {
            'sucesso': False,
            'mensagem': f'Falha ao enviar codigo via {canal}. Tente novamente.',
            'codigo': None
        }


def reenviar_otp(telemovel: str, canal: str = 'whatsapp', ip_address: str = None) -> Dict[str, Any]:
    OTPService._limpar_otp(telemovel)
    return gerar_e_enviar_otp(telemovel, canal, ip_address)
