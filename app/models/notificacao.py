"""
Modelos de Notificação e Alertas
"""
from app.extensions import db
from app.models.base import aware_utcnow


class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    data_leitura = db.Column(db.DateTime(timezone=True))
    
    def marcar_como_lida(self):
        self.lida = True
        self.data_leitura = aware_utcnow()


class AlertaPreferencia(db.Model):
    __tablename__ = 'alertas_preferencias'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    tipo_alerta = db.Column(db.String(50), nullable=False)
    criterios = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
