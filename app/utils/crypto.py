"""
Utilitário de Criptografia para Dados Sensíveis (LGPD/GDPR)
Criptografa NIF, IBAN e outros dados financeiros
"""
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64


class CryptoService:
    """Serviço de criptografia AES-256 para dados sensíveis"""
    
    def __init__(self, secret_key: str = None):
        if secret_key is None:
            secret_key = os.environ.get('SECRET_KEY')
        if not secret_key:
            raise ValueError("SECRET_KEY necessária para criptografia")
        
        # Derivar chave de 32 bytes usando PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'agrokongo_salt_v1',  # Em produção, usar salt único por instalação
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        self.cipher = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Criptografa texto e retorna string base64"""
        if not plaintext:
            return None
        encrypted = self.cipher.encrypt(plaintext.encode())
        return encrypted.decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """Descriptografa string base64 e retorna texto"""
        if not ciphertext:
            return None
        decrypted = self.cipher.decrypt(ciphertext.encode())
        return decrypted.decode('utf-8')


# Instância global
_crypto = None

def get_crypto():
    """Retorna instância singleton do serviço de criptografia"""
    global _crypto
    if _crypto is None:
        _crypto = CryptoService()
    return _crypto
