"""
Helper para criptografia de dados sensíveis (LGPD/PCI-DSS)
Implementa criptografia AES para campos como NIF, IBAN, etc.
"""
import os
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app
from typing import Optional


class DataEncryption:
    """
    Classe para criptografia de dados sensíveis usando Fernet (AES).
    Alternativa ao SQLAlchemy-Utils para maior controle.
    """
    
    @staticmethod
    def _get_cipher() -> Fernet:
        """Retorna instância do Fernet baseada na SECRET_KEY"""
        secret_key = current_app.config.get('SECRET_KEY')
        if not secret_key:
            raise ValueError("SECRET_KEY não configurada")
        
        # Deriva uma chave de 32 bytes usando PBKDF2 (via PBKDF2HMAC)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'agrokongo_lgpd_salt',  # Salt fixo para consistência
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return Fernet(key)
    
    @staticmethod
    def encrypt(plain_text: str) -> str:
        """
        Criptografa um texto plano.
        
        Args:
            plain_text: Texto a ser criptografado
            
        Returns:
            Texto criptografado em base64
        """
        if not plain_text:
            return None
            
        cipher = DataEncryption._get_cipher()
        encrypted = cipher.encrypt(plain_text.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @staticmethod
    def decrypt(encrypted_text: str) -> Optional[str]:
        """
        Descriptografa um texto.
        
        Args:
            encrypted_text: Texto criptografado em base64
            
        Returns:
            Texto descriptografado ou None se inválido
        """
        if not encrypted_text:
            return None
            
        try:
            cipher = DataEncryption._get_cipher()
            decoded = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # Retorna o texto original se não for possível descriptografar
            # (para compatibilidade com dados não criptografados)
            return encrypted_text
    
    @staticmethod
    def hash_sensitive(data: str) -> str:
        """
        Cria um hash irreversível para dados sensíveis (para lookup sem exposição).
        Útil para busca por NIF/IBAN sem armazenar o valor real.
        """
        if not data:
            return None
        return hashlib.sha256(data.upper().encode()).hexdigest()


class CampoCriptografado:
    """
    Descriptor para campos criptografados em modelos SQLAlchemy.
    Uso:
        class Usuario(db.Model):
            nif_criptografado = CampoCriptografado('nif')
            iban_criptografado = CampoCriptografado('iban')
    """
    
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.internal_name = f'_{field_name}_encrypted'
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
            
        encrypted_value = getattr(obj, self.internal_name, None)
        if encrypted_value:
            return DataEncryption.decrypt(encrypted_value)
        return None
    
    def __set__(self, obj, value):
        if value:
            encrypted = DataEncryption.encrypt(value)
            setattr(obj, self.internal_name, encrypted)
        else:
            setattr(obj, self.internal_name, None)


def get_client_ip(request) -> str:
    """Obtém o IP real do cliente, considerando proxies"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr
