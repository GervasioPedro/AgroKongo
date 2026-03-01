"""
Modelos Financeiros - Carteira e Movimentações
"""
from decimal import Decimal
from app.extensions import db
from app.models.base import aware_utcnow, StatusConta


class Carteira(db.Model):
    __tablename__ = 'carteiras'
    __table_args__ = (
        db.CheckConstraint('saldo_disponivel >= 0', name='ck_saldo_disponivel_pos'),
        db.CheckConstraint('saldo_bloqueado >= 0', name='ck_saldo_bloqueado_pos'),
        db.UniqueConstraint('usuario_id', name='uq_carteira_usuario'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, unique=True)
    saldo_disponivel = db.Column(db.Numeric(14, 2), default=Decimal('0.00'), nullable=False)
    saldo_bloqueado = db.Column(db.Numeric(14, 2), default=Decimal('0.00'), nullable=False)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow, nullable=False)
    data_ultima_atualizacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow, nullable=False)
    usuario = db.relationship('Usuario', backref=db.backref('carteira', uselist=False, lazy='select'))
    
    def creditar(self, valor: Decimal, motivo: str = None):
        if valor <= 0:
            raise ValueError("Valor de crédito deve ser positivo")
        saldo_anterior = self.saldo_disponivel
        self.saldo_disponivel += valor
        self.data_ultima_atualizacao = aware_utcnow()
        movimentacao = MovimentacaoFinanceira(
            usuario_id=self.usuario_id,
            valor=valor,
            tipo='credito',
            descricao=motivo or f"Crédito de {valor} Kz",
            saldo_anterior=saldo_anterior,
            saldo_posterior=self.saldo_disponivel
        )
        db.session.add(movimentacao)
        db.session.commit()
    
    def debitar(self, valor: Decimal, motivo: str = None):
        if valor <= 0:
            raise ValueError("Valor de débito deve ser positivo")
        if self.saldo_disponivel < valor:
            raise ValueError("Saldo insuficiente para débito")
        saldo_anterior = self.saldo_disponivel
        self.saldo_disponivel -= valor
        self.data_ultima_atualizacao = aware_utcnow()
        movimentacao = MovimentacaoFinanceira(
            usuario_id=self.usuario_id,
            valor=valor,
            tipo='debito',
            descricao=motivo or f"Débito de {valor} Kz",
            saldo_anterior=saldo_anterior,
            saldo_posterior=self.saldo_disponivel
        )
        db.session.add(movimentacao)
        db.session.commit()
    
    def get_saldo_total(self):
        return self.saldo_disponivel + self.saldo_bloqueado
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'saldo_disponivel': float(self.saldo_disponivel),
            'saldo_bloqueado': float(self.saldo_bloqueado),
            'saldo_total': float(self.get_saldo_total()),
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_ultima_atualizacao': self.data_ultima_atualizacao.isoformat() if self.data_ultima_atualizacao else None
        }


class MovimentacaoFinanceira(db.Model):
    __tablename__ = 'movimentacoes_financeiras'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    valor = db.Column(db.Numeric(14, 2), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.Text)
    saldo_anterior = db.Column(db.Numeric(14, 2))
    saldo_posterior = db.Column(db.Numeric(14, 2))
    referencia_transacao = db.Column(db.String(50))
    data_movimentacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
