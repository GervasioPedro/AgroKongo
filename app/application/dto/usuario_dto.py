# app/application/dto/usuario_dto.py
"""
DTOs para Usuários - Validação com Pydantic

Este módulo define os Data Transfer Objects para operações
relacionadas a usuários, com validação automática usando Pydantic.
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class UsuarioCreateDTO(BaseModel):
    """DTO para criação de novo usuário."""
    
    nome: str = Field(..., min_length=3, max_length=100)
    telemovel: str = Field(..., pattern=r'^9[1-9]\d{7}$')
    email: EmailStr
    senha: str = Field(..., min_length=12)
    tipo: str = Field(..., pattern=r'^(produtor|comprador)$')
    termos: bool = Field(..., eq=True)
    
    @field_validator('senha')
    @classmethod
    def senha_forte(cls, v: str) -> str:
        """Valida que a senha atende aos requisitos de força."""
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos uma maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos uma minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        if not any(c in '@$!%*?&' for c in v):
            raise ValueError('Senha deve conter pelo menos um símbolo')
        return v
    
    model_config = {
        'json_schema_extra': {
            'example': {
                'nome': 'João da Silva',
                'telemovel': '921234567',
                'email': 'joao@exemplo.ao',
                'senha': 'SenhaForte123!',
                'tipo': 'produtor',
                'termos': True
            }
        }
    }


class UsuarioUpdateDTO(BaseModel):
    """DTO para atualização de dados do usuário."""
    
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    provincia_id: Optional[int] = Field(None, gt=0)
    municipio_id: Optional[int] = Field(None, gt=0)
    foto_perfil: Optional[str] = None


class PerfilKycDTO(BaseModel):
    """DTO para completamento do perfil KYC."""
    
    nif: str = Field(..., pattern=r'^\d{10}$')
    iban: str = Field(..., pattern=r'^AO\d{23}$')
    provincia_id: int = Field(..., gt=0)
    municipio_id: int = Field(..., gt=0)
    documento_pdf: Optional[str] = None
    foto_perfil: Optional[str] = None


class UsuarioResponseDTO(BaseModel):
    """DTO para resposta de dados do usuário (sem dados sensíveis)."""
    
    id: int
    nome: str
    telemovel: str
    email: Optional[str] = None
    tipo: str
    conta_validada: bool
    perfil_completo: bool
    provincia: Optional[str] = None
    municipio: Optional[str] = None
    foto_perfil: Optional[str] = None
    data_cadastro: datetime
    
    model_config = {
        'from_attributes': True
    }


class UsuarioAdminResponseDTO(UsuarioResponseDTO):
    """DTO estendido para resposta administrativa."""
    
    nif_mascarado: Optional[str] = None
    iban_mascarado: Optional[str] = None
    ativo: bool
    ultimo_login: Optional[datetime] = None
    vendas_concluidas: int = 0


class LoginRequestDTO(BaseModel):
    """DTO para requisição de login."""
    
    telemovel: str = Field(..., pattern=r'^9[1-9]\d{7}$')
    senha: str = Field(..., min_length=6)
    
    model_config = {
        'json_schema_extra': {
            'example': {
                'telemovel': '921234567',
                'senha': 'MinhaSenha123!'
            }
        }
    }


class ChangePasswordDTO(BaseModel):
    """DTO para alteração de senha."""
    
    senha_atual: str = Field(..., min_length=6)
    nova_senha: str = Field(..., min_length=12)
    
    @field_validator('nova_senha')
    @classmethod
    def senha_forte(cls, v: str) -> str:
        """Valida que a senha atende aos requisitos de força."""
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos uma maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos uma minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v
