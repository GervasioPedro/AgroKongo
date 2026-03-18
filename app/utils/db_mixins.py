"""
Mixins reutilizáveis para modelos SQLAlchemy.
Inclui soft delete, timestamps automáticos e auditoria.
"""
from datetime import datetime, timezone
from sqlalchemy import event


class SoftDeleteMixin:
    """
    Adiciona funcionalidade de soft delete a modelos.
    Em vez de remover permanentemente, marca como deletado.
    """
    deleted_at = None  # Será criado como Column nas classes filhas
    
    def soft_delete(self):
        """Marca o registo como deletado."""
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """Restaura o registo deletado."""
        self.deleted_at = None
    
    @property
    def is_deleted(self):
        """Verifica se o registo está deletado."""
        return self.deleted_at is not None
    
    @classmethod
    def active(cls):
        """
        Filtro para registos não deletados.
        Uso: Usuario.active().filter_by(tipo='produtor')
        """
        from app.extensions import db
        return cls.query.filter_by(deleted_at=None)
    
    @classmethod
    def deleted(cls):
        """
        Filtro para registos deletados.
        Uso: Transacao.deleted().all()
        """
        from app.extensions import db
        return cls.query.filter(cls.deleted_at != None)


class TimestampMixin:
    """
    Adiciona timestamps automáticos (created_at, updated_at).
    """
    created_at = None  # Será criado como Column nas classes filhas
    updated_at = None
    
    @staticmethod
    def _update_updated_at(mapper, connection, target):
        """Atualiza updated_at antes de update."""
        target.updated_at = datetime.now(timezone.utc)


def init_soft_delete_listener(model_class):
    """
    Configura listener para filtrar automaticamente registos deletados.
    Deve ser chamado após definir o modelo.
    
    Uso:
        class Transacao(db.Model, SoftDeleteMixin):
            __tablename__ = 'transacoes'
        
        init_soft_delete_listener(Transacao)
    """
    @event.listens_for(model_class, "before_delete")
    def intercept_delete(mapper, connection, target):
        # Previne delete físico acidental para modelos financeiros
        if hasattr(target, 'deleted_at'):
            from flask import current_app
            current_app.logger.warning(
                f"Tentativa de DELETE físico em {model_class.__name__} ID={target.id}. "
                "Use soft_delete() em vez disso."
            )
            # Nota: Para bloquear completamente, levantaria exceção aqui


def add_timestamp_columns(model_class):
    """
    Adiciona colunas created_at e updated_at dinamicamente.
    Deve ser chamado na definição do modelo.
    """
    from app.extensions import db
    from sqlalchemy import Column, DateTime
    
    model_class.created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    model_class.updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
