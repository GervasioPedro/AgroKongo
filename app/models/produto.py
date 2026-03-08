"""
Modelos de Produto e Safra
"""
from typing import Dict, Any
from decimal import Decimal
from sqlalchemy import Index
from app.extensions import db
from app.models.base import aware_utcnow

class Produto(db.Model):
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.Text)
    imagem_url = db.Column(db.String(255))
    safras = db.relationship('Safra', backref='produto', lazy='select', cascade="all, delete-orphan")


class Safra(db.Model):
    __tablename__ = 'safras'
    __table_args__ = (
        Index('idx_safra_produto_status', 'produto_id', 'status'),
        Index('idx_safra_produtor_id', 'produtor_id'),
        Index('idx_safra_regiao_status', 'localizacao', 'status'),
        Index('idx_safra_data_plantio', 'data_plantio'),
        Index('idx_safra_preco', 'preco_por_unidade'),
    )

    id = db.Column(db.Integer, primary_key=True)
    produtor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id', ondelete='CASCADE'), nullable=False)
    
    quantidade_disponivel = db.Column(db.Numeric(14, 3), nullable=False)
    preco_por_unidade = db.Column(db.Numeric(14, 2), nullable=False)
    
    descricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    imagem_url = db.Column(db.String(255)) # Campo para imagem da safra
    
    data_plantio = db.Column(db.Date)
    data_previsao_colheita = db.Column(db.Date)
    
    localizacao = db.Column(db.String(255))
    status = db.Column(db.String(20), default='disponivel')
    
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    data_atualizacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)
    
    transacoes = db.relationship('Transacao', back_populates='safra', lazy='select', cascade="all, delete-orphan")
    
    def valor_total(self) -> Decimal:
        return self.quantidade_disponivel * self.preco_por_unidade
