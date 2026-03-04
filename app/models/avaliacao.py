"""
Modelo de Avaliação de Transações
"""
from sqlalchemy_serializer import SerializerMixin
from app.extensions import db
from app.models.base import aware_utcnow
from sqlalchemy import ForeignKey

class Avaliacao(db.Model, SerializerMixin):
    __tablename__ = 'avaliacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Adicionar nomes às constraints para compatibilidade com SQLite/Alembic
    transacao_id = db.Column(db.Integer, ForeignKey('transacoes.id', ondelete='CASCADE', name='fk_avaliacao_transacao'), nullable=False, unique=True)
    produtor_id = db.Column(db.Integer, ForeignKey('usuarios.id', ondelete='CASCADE', name='fk_avaliacao_produtor'), nullable=False)
    comprador_id = db.Column(db.Integer, ForeignKey('usuarios.id', ondelete='CASCADE', name='fk_avaliacao_comprador'), nullable=False)
    
    estrelas = db.Column(db.Integer, nullable=False)
    comentario = db.Column(db.Text)
    
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)

    # Relacionamentos
    transacao = db.relationship('Transacao', backref='avaliacao', uselist=False)
    produtor = db.relationship('Usuario', foreign_keys=[produtor_id])
    comprador = db.relationship('Usuario', foreign_keys=[comprador_id])
