"""
Modelo de Transação
"""
import uuid
from typing import Dict, Any, Optional
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import Index

from app.extensions import db
from app.models.base import aware_utcnow, TransactionStatus


class Transacao(db.Model):
    __tablename__ = 'transacoes'
    __table_args__ = (
        Index('idx_trans_status_comprador', 'status', 'comprador_id'),
        Index('idx_trans_status_vendedor', 'status', 'vendedor_id'),
        Index('idx_trans_data_status', 'data_criacao', 'status'),
        Index('idx_trans_fatura_ref', 'fatura_ref'),
        Index('idx_trans_safra', 'safra_id'),
        Index('idx_trans_data_criacao', 'data_criacao'),
        Index('idx_trans_uuid', 'uuid'),
    )

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    fatura_ref = db.Column(db.String(50), unique=True, nullable=False, index=True)
    safra_id = db.Column(db.Integer, db.ForeignKey('safras.id', ondelete='CASCADE'), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    quantidade_comprada = db.Column(db.Numeric(14, 3), nullable=False)
    valor_total_pago = db.Column(db.Numeric(14, 2), nullable=False)
    comissao_plataforma = db.Column(db.Numeric(14, 2), default=0.00)
    valor_liquido_vendedor = db.Column(db.Numeric(14, 2), default=0.00)
    status = db.Column(db.String(20), default=TransactionStatus.PENDENTE, nullable=False)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    data_pagamento_escrow = db.Column(db.DateTime(timezone=True))
    data_envio = db.Column(db.DateTime(timezone=True))
    previsao_entrega = db.Column(db.DateTime(timezone=True))
    data_entrega = db.Column(db.DateTime(timezone=True))
    data_liquidacao = db.Column(db.DateTime(timezone=True))
    comprovativo_path = db.Column(db.String(255))
    transferencia_concluida = db.Column(db.Boolean, default=False)
    observacoes = db.Column(db.Text)
    historico_status = db.relationship('HistoricoStatus', backref='transacao', lazy='select', cascade="all, delete-orphan")
    
    # Relacionamentos para joinedload
    safra = db.relationship('Safra', back_populates='transacoes', lazy='select')
    comprador = db.relationship('Usuario', foreign_keys=[comprador_id], back_populates='transacoes_como_comprador', lazy='select')
    vendedor = db.relationship('Usuario', foreign_keys=[vendedor_id], back_populates='transacoes_como_vendedor', lazy='select')

    def recalcular_financeiro(self, taxa_plataforma: Optional[Decimal] = None) -> None:
        if taxa_plataforma is None:
            from app.models.auditoria import ConfiguracaoSistema
            taxa = ConfiguracaoSistema.obter_valor_decimal('TAXA_PLATAFORMA', padrao=Decimal('0.10'))
        else:
            taxa = taxa_plataforma
        
        if not isinstance(taxa, Decimal):
            taxa = Decimal(str(taxa))
        
        self.comissao_plataforma = (self.valor_total_pago * taxa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        self.valor_liquido_vendedor = self.valor_total_pago - self.comissao_plataforma
    
    def calcular_janela_logistica(self) -> None:
        if self.data_envio:
            self.previsao_entrega = self.data_envio + timedelta(days=3)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'uuid': self.uuid,
            'fatura_ref': self.fatura_ref,
            'status': self.status,
            'quantidade_comprada': float(self.quantidade_comprada) if self.quantidade_comprada else 0,
            'valor_total_pago': float(self.valor_total_pago) if self.valor_total_pago else 0,
            'comissao_plataforma': float(self.comissao_plataforma) if self.comissao_plataforma else 0,
            'valor_liquido_vendedor': float(self.valor_liquido_vendedor) if self.valor_liquido_vendedor else 0,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'previsao_entrega': self.previsao_entrega.isoformat() if self.previsao_entrega else None
        }


class HistoricoStatus(db.Model):
    __tablename__ = 'historico_status'
    __table_args__ = (
        # Índices para performance em auditoria
        Index('idx_historico_status_transacao', 'transacao_id'),
        Index('idx_historico_status_data', 'data_alteracao'),
    )
    id = db.Column(db.Integer, primary_key=True)
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacoes.id', ondelete='CASCADE'), nullable=False)
    status_anterior = db.Column(db.String(20))
    status_novo = db.Column(db.String(20), nullable=False)
    observacoes = db.Column(db.Text)
    data_alteracao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    usuario_alteracao = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
