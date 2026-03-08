"""
Modelo de Disputa
"""
from datetime import timedelta, datetime, timezone
from decimal import Decimal
from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.base import aware_utcnow, TransactionStatus


class Disputa(db.Model):
    __tablename__ = 'disputas'
    __table_args__ = (
        CheckConstraint('motivo IS NOT NULL AND motivo != ""', name='ck_motivo_obrigatorio'),
        Index('idx_disputa_transacao', 'transacao_id'),
        Index('idx_disputa_status', 'status'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacoes.id', ondelete='CASCADE'), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    evidencia_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='aberta', index=True)
    data_abertura = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    data_resolucao = db.Column(db.DateTime(timezone=True))
    admin_responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    decisao_justificativa = db.Column(db.Text)
    taxa_administrativa = db.Column(db.Numeric(14, 2), default=0.00)
    
    transacao = db.relationship('Transacao', backref=db.backref('disputa', uselist=False))
    comprador = db.relationship('Usuario', foreign_keys=[comprador_id], backref='disputas_abertas')
    admin_responsavel = db.relationship('Usuario', foreign_keys=[admin_responsavel_id])
    
    def pode_abrir_disputa(self):
        if self.transacao.status not in [TransactionStatus.ENVIADO, TransactionStatus.ESCROW]:
            return False, "Status inválido para disputa"
        if not self.transacao.previsao_entrega:
            return False, "Previsão de entrega não definida"
        limite_minimo = self.transacao.previsao_entrega + timedelta(hours=24)
        agora = datetime.now(timezone.utc)
        if agora < limite_minimo:
            return False, "Aguarde 24h após a previsão de entrega"
        return True, "Disputa pode ser aberta"
    
    def calcular_taxa_administrativa(self):
        if self.transacao:
            taxa_percentual = Decimal('0.05')
            self.taxa_administrativa = (self.transacao.valor_total_pago * taxa_percentual).quantize(Decimal('0.01'))
        return self.taxa_administrativa
