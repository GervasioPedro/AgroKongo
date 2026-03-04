"""
Modelos de Usuário com Criptografia LGPD
"""
import re
from typing import List, Dict, Any
from decimal import Decimal
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property

from app.extensions import db, login_manager
from app.models.base import aware_utcnow, StatusConta


class Provincia(db.Model):
    __tablename__ = 'provincias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    municipios = db.relationship('Municipio', backref='provincia', lazy='select', cascade="all, delete-orphan")


class Municipio(db.Model):
    __tablename__ = 'municipios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id', ondelete='CASCADE'), nullable=False)


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telemovel = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    senha = db.Column(db.String(255), nullable=False)
    senha_hash = db.Column(db.String(255))
    tipo = db.Column(db.String(20), nullable=False, default='comprador')
    
    # Campos criptografados (armazenam dados criptografados)
    _nif_encrypted = db.Column('nif', db.String(500), index=True)
    _iban_encrypted = db.Column('iban', db.String(500))
    
    foto_perfil = db.Column(db.String(255))
    documento_pdf = db.Column(db.String(255))
    perfil_completo = db.Column(db.Boolean, default=False)
    conta_validada = db.Column(db.Boolean, default=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id', ondelete='SET NULL'))
    municipio_id = db.Column(db.Integer, db.ForeignKey('municipios.id', ondelete='SET NULL'))
    data_cadastro = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    saldo_disponivel = db.Column(db.Numeric(14, 2), default=0.00)
    vendas_concluidas = db.Column(db.Integer, default=0)
    principal_cultura = db.Column(db.String(100))
    experiencia_anos = db.Column(db.Integer)
    certificacoes = db.Column(db.Text)
    localizacao_fazenda = db.Column(db.String(255))
    preferencias_compra = db.Column(db.Text)
    limite_credito = db.Column(db.Numeric(14, 2), default=0.00)
    ultimo_login = db.Column(db.DateTime(timezone=True))
    ip_ultimo_login = db.Column(db.String(45))
    ativo = db.Column(db.Boolean, default=True)
    data_bloqueio = db.Column(db.DateTime(timezone=True))
    motivo_bloqueio = db.Column(db.Text)
    
    safras_criadas = db.relationship('Safra', backref='produtor', lazy='select', cascade="all, delete-orphan")
    transacoes_como_comprador = db.relationship('Transacao', foreign_keys='Transacao.comprador_id', backref='comprador', lazy='select')
    transacoes_como_vendedor = db.relationship('Transacao', foreign_keys='Transacao.vendedor_id', backref='vendedor', lazy='select')
    notificacoes = db.relationship('Notificacao', backref='usuario', lazy='select', cascade="all, delete-orphan")
    logs_auditoria = db.relationship('LogAuditoria', backref='usuario', lazy='select', cascade="all, delete-orphan")
    
    @hybrid_property
    def nif(self) -> str:
        """Descriptografa NIF ao acessar"""
        if not self._nif_encrypted:
            return None
        try:
            from app.utils.crypto import get_crypto
            return get_crypto().decrypt(self._nif_encrypted)
        except Exception:
            return None
    
    @nif.setter
    def nif(self, value: str):
        """Criptografa NIF ao definir"""
        if not value:
            self._nif_encrypted = None
            return
        try:
            from app.utils.crypto import get_crypto
            self._nif_encrypted = get_crypto().encrypt(value)
        except Exception as e:
            raise ValueError(f"Erro ao criptografar NIF: {e}")
    
    @hybrid_property
    def iban(self) -> str:
        """Descriptografa IBAN ao acessar"""
        if not self._iban_encrypted:
            return None
        try:
            from app.utils.crypto import get_crypto
            return get_crypto().decrypt(self._iban_encrypted)
        except Exception:
            return None
    
    @iban.setter
    def iban(self, value: str):
        """Criptografa IBAN ao definir"""
        if not value:
            self._iban_encrypted = None
            return
        try:
            from app.utils.crypto import get_crypto
            self._iban_encrypted = get_crypto().encrypt(value)
        except Exception as e:
            raise ValueError(f"Erro ao criptografar IBAN: {e}")
    
    @validates('telemovel')
    def validate_telemovel(self, key: str, telemovel: str) -> str:
        num = re.sub(r'\D', '', telemovel)
        if num.startswith('244'): num = num[3:]
        if not re.match(r'^9\d{8}$', num): raise ValueError("Formato AO inválido.")
        return num
    
    def set_senha(self, senha: str) -> None:
        hashed = generate_password_hash(senha)
        self.senha = hashed
        self.senha_hash = hashed
    
    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha, senha)
    
    def verificar_e_atualizar_perfil(self) -> bool:
        campos_comuns = [self.nome, self.nif, self.provincia_id, self.municipio_id]
        if not all(campos_comuns):
            return False
        if self.tipo == 'produtor' and not self.iban:
            return False
        self.perfil_completo = True
        return True
    
    def notificacoes_nao_lidas(self) -> int:
        if hasattr(self, 'notificacoes'):
            return len([n for n in self.notificacoes if not n.lida])
        return 0
    
    def ultimas_notificacoes(self, limite: int = 5) -> List:
        if not hasattr(self, 'notificacoes') or self.notificacoes is None:
            return []
        try:
            notificacoes = sorted(list(self.notificacoes), key=lambda n: n.data_criacao or aware_utcnow(), reverse=True)
            return notificacoes[:limite]
        except Exception:
            return []
    
    def atualizar_saldo(self, valor: Decimal) -> None:
        self.saldo_disponivel = Usuario.saldo_disponivel + valor
    
    def obter_carteira(self):
        if not hasattr(self, 'carteira') or self.carteira is None:
            from app.models.financeiro import Carteira
            carteira = Carteira(usuario_id=self.id, saldo_disponivel=Decimal('0.00'))
            db.session.add(carteira)
            return carteira
        return self.carteira
    
    def pode_criar_anuncios(self) -> bool:
        return self.conta_validada and self.tipo == 'produtor'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'nome': self.nome,
            'telemovel': self.telemovel,
            'email': self.email,
            'tipo': self.tipo,
            'perfil_completo': self.perfil_completo,
            'conta_validada': self.conta_validada,
            'saldo_disponivel': float(self.saldo_disponivel),
            'vendas_concluidas': self.vendas_concluidas,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None
        }


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
