# app/domain/value_objects/campos_cifrados.py
"""
Mixin para campos cifrados - Criptografia de dados sensíveis

Este módulo implementa a proteção de dados sensíveis conforma LGPD/LPDP (Angola)
e GDPR (Europa). Utiliza SQLAlchemy-Utils para criptografia em nível de campo.

Artigo 46º da LPDP: "Os responsáveis pelo tratamento devem adoptar 
medidas de segurança, técnicas e administrativas..."

Uso:
    from app.domain.value_objects import CampoCifradoMixin
    
    class Usuario(db.Model, CampoCifradoMixin):
        nif = db.Column(campo_cifrado('nif', String(20)))
        iban = db.Column(campo_cifrado('iban', String(34)))
"""
from functools import lru_cache
from typing import Any, Optional
import os


class CampoCifradoMixin:
    """
    Mixin que fornece métodos para acesso seguro a campos cifrados.
    
    Este mixin deve ser usado em conjunto com SQLAlchemy-Utils EncryptedType.
    A chave de criptografia é derivada da SECRET_KEY do Flask.
    """
    
    @classmethod
    def get_secret_key(cls) -> str:
        """
        Obtém a chave de segredo para criptografia.
        
        Returns:
            String com a chave de segredo
        """
        from flask import current_app
        try:
            # Tenta obter da configuração do Flask
            secret = current_app.config.get('SECRET_KEY')
            if not secret:
                raise ValueError("SECRET_KEY não configurada")
            return secret
        except RuntimeError:
            # Fallback para contextos sem Flask
            return os.environ.get('SECRET_KEY', 'fallback-key-change-in-prod')


# ============================================================
# Factory para criação de campos cifrados
# ============================================================

@lru_cache(maxsize=1)
def get_encryption_key() -> str:
    """
    Obtém a chave de criptografia para SQLAlchemy-Utils.
    
    Returns:
        Chave de criptografia
    """
    from flask import current_app
    try:
        return current_app.config.get('SECRET_KEY', 'default-key')
    except RuntimeError:
        return os.environ.get('SECRET_KEY', 'fallback-key')


def campo_cifrado(nome_campo: str, tipo_coluna, **kwargs):
    """
    Factory para criar campos cifrados.
    
    Args:
        nome_campo: Nome do campo (usado para logging)
        tipo_coluna: Tipo da coluna SQLAlchemy
        **kwargs: Argumentos adicionais para EncryptedType
        
    Returns:
        Coluna SQLAlchemy com criptografia
    """
    try:
        from sqlalchemy_utils import EncryptedType
        
        return EncryptedType(
            tipo_coluna,
            get_encryption_key(),
            **kwargs
        )
    except ImportError:
        # Fallback se sqlalchemy-utils não estiver instalado
        # Em produção, isto NÃO deve acontecer
        import warnings
        warnings.warn(
            f"sqlalchemy-utils não instalado. Campo {nome_campo} não será cifrado!",
            RuntimeWarning
        )
        return tipo_coluna


# ============================================================
# Decorator para métodos de acesso seguro
# ============================================================

def propriedade_segura(nome_campo: str):
    """
    Decorator para criar propriedades seguras com mascaramento.
    
    Args:
        nome_campo: Nome do campo a ser mascarado
        
    Returns:
        Property com getter que mascara dados sensíveis
    """
    def decorator(func):
        def wrapper(self):
            valor = func(self)
            if valor is None:
                return None
            
            # Mascarar baseado no tipo de campo
            if nome_campo in ['nif', 'iban']:
                if len(valor) >= 4:
                    return '*' * (len(valor) - 4) + valor[-4:]
            return valor
        
        return property(wrapper)
    return decorator


# ============================================================
# Funções utilitárias para migração
# ============================================================

def criar_coluna_cifrada(nome: str, tipo: str, nullable: bool = True):
    """
    Cria uma definição de coluna cifrada para migração Alembic.
    
    Args:
        nome: Nome da coluna
        tipo: Tipo SQL (ex: 'String(20)')
        nullable: Se a coluna pode ser nula
        
    Returns:
        String com definição de coluna
    """
    return f"""
    # {nome} - Campo cifrado (LGPD Art. 46)
    # Requer sqlalchemy-utils instalado
    {nome} = db.Column(EncryptedType(db.{tipo}, '{get_encryption_key()}'{', nullable=False' if not nullable else ''}))
    """


# ============================================================
# Validação de conformidade LGPD
# ============================================================

class LGPDCompliance:
    """
    Classe utilitária para validação de conformidade LGPD.
    
    Verifica se os campos sensíveis estão corretamente configurados.
    """
    
    CAMPOS_SENSIVEIS = ['nif', 'iban', 'documento_pdf', 'senha_hash']
    
    @classmethod
    def verificar_modelo(cls, modelo) -> dict:
        """
        Verifica se um modelo tem campos sensíveis protegidos.
        
        Args:
            modelo: Classe do modelo SQLAlchemy
            
        Returns:
            Dicionário com resultados da verificação
        """
        resultados = {
            'modelo': modelo.__name__,
            'campos_protegidos': [],
            'campos_em_risco': [],
            'conformidade': True
        }
        
        for nome_coluna in cls.CAMPOS_SENSITIVEIS:
            if hasattr(modelo, nome_coluna):
                coluna = getattr(modelo, nome_coluna)
                # Verifica se é um campo cifrado
                if hasattr(coluna, 'type') and 'EncryptedType' in str(type(coluna.type)):
                    resultados['campos_protegidos'].append(nome_coluna)
                else:
                    resultados['campos_em_risco'].append(nome_coluna)
                    resultados['conformidade'] = False
        
        return resultados
