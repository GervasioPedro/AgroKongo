import decimal
from decimal import Decimal
from app.extensions import db
from app.models.base import aware_utcnow


class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    acao = db.Column(db.String(50), nullable=False)
    detalhes = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    data_acao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)


class ConfiguracaoSistema(db.Model):
    __tablename__ = 'configuracoes_sistema'
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Text)
    descricao = db.Column(db.Text)
    data_atualizacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)
    
    @classmethod
    def obter_valor_decimal(cls, chave: str, padrao: Decimal = Decimal('0.00')) -> Decimal:
        try:
            config = cls.query.filter_by(chave=chave).first()
            if config and config.valor:
                valor_decimal = Decimal(str(config.valor))
                return valor_decimal
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            try:
                from flask import current_app
                current_app.logger.warning(f"Erro ao converter configuracao '{chave}': {e}")
            except RuntimeError:
                import sys
                print(f"Erro ao converter configuracao '{chave}': {e}", file=sys.stderr)
        except Exception as e:
            try:
                from flask import current_app
                current_app.logger.error(f"Erro inesperado ao obter configuracao '{chave}': {e}")
            except RuntimeError:
                import sys
                print(f"Erro inesperado ao obter configuracao '{chave}': {e}", file=sys.stderr)
        
        return padrao
