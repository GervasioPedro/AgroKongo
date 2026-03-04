# app/application/dto/transacao_dto.py
"""
DTOs para Transações - Validação com Pydantic

Este módulo define os Data Transfer Objects para operações
relacionadas a transações (Escrow), com validação automática.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class StatusTransacao(str, Enum):
    """Enum para status de transação."""
    PENDENTE = "PENDENTE"
    ANALISE = "ANALISE"
    ESCROW = "ESCROW"
    ENVIADO = "ENVIADO"
    ENTREGUE = "ENTREGUE"
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"
    DISPUTA = "DISPUTA"


class TransacaoCreateDTO(BaseModel):
    """DTO para criação de nova transação (reserva)."""
    
    safra_id: int = Field(..., gt=0)
    quantidade: Decimal = Field(..., gt=0, decimal_places=3)
    
    @field_validator('quantidade')
    @classmethod
    def validar_quantidade(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Quantidade deve ser maior que zero')
        return v
    
    model_config = {
        'json_schema_extra': {
            'example': {
                'safra_id': 1,
                'quantidade': 100.0
            }
        }
    }


class ComprovativoPagamentoDTO(BaseModel):
    """DTO para submissão de comprovativo de pagamento."""
    
    transacao_id: int = Field(..., gt=0)
    valor_pago: Decimal = Field(..., gt=0)
    data_pagamento: datetime
    comprovativo_filename: str
    
    @field_validator('valor_pago')
    @classmethod
    def validar_valor(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Valor deve ser maior que zero')
        return v
    
    model_config = {
        'json_schema_extra': {
            'example': {
                'transacao_id': 123,
                'valor_pago': 50000.00,
                'data_pagamento': '2026-03-04T10:00:00Z',
                'comprovativo_filename': 'comprovativo_123.webp'
            }
        }
    }


class ValidarPagamentoDTO(BaseModel):
    """DTO para validação de pagamento (Admin)."""
    
    transacao_id: int = Field(..., gt=0)
    admin_id: int = Field(..., gt=0)
    aprova: bool


class LiberarPagamentoDTO(BaseModel):
    """DTO para liberação de pagamento ao vendedor."""
    
    transacao_id: int = Field(..., gt=0)
    admin_id: Optional[int] = None


class ResolverDisputaDTO(BaseModel):
    """DTO para resolução de disputa (Admin)."""
    
    transacao_id: int = Field(..., gt=0)
    admin_id: int = Field(..., gt=0)
    decisao: str = Field(..., pattern=r'^(comprador|vendedor)$')
    motivo: str = Field(..., min_length=20, max_length=1000)


class TransacaoResponseDTO(BaseModel):
    """DTO para resposta de transação."""
    
    id: int
    fatura_ref: str
    status: StatusTransacao
    quantidade_comprada: Decimal
    valor_total_pago: Decimal
    comissao_plataforma: Decimal
    valor_liquido_vendedor: Decimal
    data_criacao: datetime
    data_pagamento_escrow: Optional[datetime] = None
    data_envio: Optional[datetime] = None
    previsao_entrega: Optional[datetime] = None
    data_entrega: Optional[datetime] = None
    data_liquidacao: Optional[datetime] = None
    
    model_config = {'from_attributes': True}


class TransacaoDetalheResponseDTO(TransacaoResponseDTO):
    """DTO detalhado para transação."""
    
    produto_nome: str
    vendedor_nome: str
    comprador_nome: str
    vendedor_telemovel: str
    comprador_telemovel: str
    
    model_config = {'from_attributes': True}


class DashboardProdutorDTO(BaseModel):
    """DTO para dashboard do produtor."""
    
    receita_total: Decimal
    em_custodia: Decimal
    a_liquidar: Decimal
    disponivel: Decimal
    reservas_ativas: List[TransacaoResponse_ativas: List[TransacaoResponseDTO]
    historico: List[DTO]
    vendasTransacaoResponseDTO]
    
    model_config = {'from_attributes': True}


class DashboardCompradorDTO(BaseModel):
    """DTO para dashboard do comprador."""
    
    compras_pendentes: List[TransacaoResponseDTO]
    compras_ativas: List[TransacaoResponseDTO]
    historico_compras: List[TransacaoResponseDTO]
    saldo_em_escrow: Decimal
    
    model_config = {'from_attributes': True}


class DashboardAdminDTO(BaseModel):
    """DTO para dashboard administrativo."""
    
    total_usuarios: int
    total_transacoes: int
    receita_total: Decimal
    transacoes_pendentes: int
    transacoes_em_analise: int
    disputas_ativas: int
    usuarios_pendentes_validacao: int
    
    model_config = {'from_attributes': True}
