# app/application/dto/safra_dto.py
"""
DTOs para Safras - Validação com Pydantic

Este módulo define os Data Transfer Objects para operações
relacionadas a safras, com validação automática usando Pydantic.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class SafraCreateDTO(BaseModel):
    """DTO para criação de nova safra."""
    
    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade_disponivel: Decimal = Field(..., gt=0, decimal_places=3, description="Quantidade em kg")
    preco_por_unidade: Decimal = Field(..., gt=0, decimal_places=2, description="Preço por kg")
    descricao: Optional[str] = Field(None, max_length=1000, description="Descrição da safra")
    imagem_filename: Optional[str] = Field(None, description="Nome do ficheiro da imagem")
    
    @field_validator('quantidade_disponivel')
    @classmethod
    def validar_quantidade(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Quantidade deve ser maior que zero')
        return v
    
    @field_validator('preco_por_unidade')
    @classmethod
    def validar_preco(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Preço deve ser maior que zero')
        return v
    
    model_config = {
        'json_schema_extra': {
            'example': {
                'produto_id': 1,
                'quantidade_disponivel': 500.0,
                'preco_por_unidade': 500.00,
                'descricao': 'Safra de milho de alta qualidade',
                'imagem_filename': 'safra_123.webp'
            }
        }
    }


class SafraUpdateDTO(BaseModel):
    """DTO para atualização de safra existente."""
    
    quantidade_disponivel: Optional[Decimal] = Field(None, gt=0, decimal_places=3)
    preco_por_unidade: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    descricao: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern=r'^(disponivel|esgotado|reservado)$')
    imagem_filename: Optional[str] = None


class SafraResponseDTO(BaseModel):
    """DTO para resposta de safra."""
    
    id: int
    produto_nome: str
    produtor_nome: str
    quantidade_disponivel: Decimal
    preco_por_unidade: Decimal
    descricao: Optional[str] = None
    imagem_url: Optional[str] = None
    status: str
    data_criacao: datetime
    
    model_config = {
        'from_attributes': True
    }


class SafraDetalheResponseDTO(SafraResponseDTO):
    """DTO detalhado para safra."""
    
    produtor_telemovel: str
    produtor_localizacao: str
    transacoes_ativas: int
    avaliacao_media: Optional[float] = None
    
    model_config = {
        'from_attributes': True
    }


class FiltroSafrasDTO(BaseModel):
    """DTO para filtro de safras no mercado."""
    
    produto_id: Optional[int] = None
    provincia_id: Optional[int] = None
    municipio_id: Optional[int] = None
    preco_min: Optional[Decimal] = None
    preco_max: Optional[Decimal] = None
    limite: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)


class ProdutoCreateDTO(BaseModel):
    """DTO para criação de novo produto (admin)."""
    
    nome: str = Field(..., min_length=2, max_length=100)
    categoria: str = Field(..., min_length=2, max_length=50)
    descricao: Optional[str] = Field(None, max_length=500)
    imagem_url: Optional[str] = None
    unidade_padrao: str = Field('kg', max_length=10)


class ProdutoResponseDTO(BaseModel):
    """DTO para resposta de produto."""
    
    id: int
    nome: str
    categoria: str
    descricao: Optional[str] = None
    imagem_url: Optional[str] = None
    unidade_padrao: str
    
    model_config = {
        'from_attributes': True
    }


class ListagemSafrasResponseDTO(BaseModel):
    """DTO para listagem paginada de safras."""
    
    total: int
    safras: List[SafraResponseDTO]
    limite: int
    offset: int
    
    model_config = {
        'from_attributes': True
    }
