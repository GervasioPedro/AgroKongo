import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import CheckConstraint, func, Index
from sqlalchemy.orm import validates, relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.extensions import db, login_manager


# Helper para consistência de tempo em servidores globais
def aware_utcnow():
    return datetime.now(timezone.utc)


# --- CONSTANTES DE ESTADO ---
class TransactionStatus:
    PENDENTE = 'pendente'
    AGUARDANDO_PAGAMENTO = 'pendente_pagamento'
    ANALISE = 'pagamento_sob_analise'
    ESCROW = 'pago_escrow'
    ENVIADO = 'mercadoria_enviada'
    ENTREGUE = 'mercadoria_entregue'
    FINALIZADO = 'finalizada'
    CANCELADO = 'cancelada'
    DISPUTA = 'em_disputa'


# --- LOCALIZAÇÃO ---
class Provincia(db.Model):
    __tablename__ = 'provincias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    municipios = db.relationship('Municipio', backref='provincia', lazy='select', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Provincia {self.nome}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome
        }


class Municipio(db.Model):
    __tablename__ = 'municipios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f'<Municipio {self.nome}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'provincia_id': self.provincia_id
        }


# --- UTILIZADORES ---
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telemovel = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False, index=True)  # 'admin', 'produtor', 'comprador'

    nif = db.Column(db.String(20), unique=True)
    iban = db.Column(db.String(34))

    rating_vendedor = db.Column(db.Numeric(3, 2), default=5.00)
    vendas_concluidas = db.Column(db.Integer, default=0)

    foto_perfil = db.Column(db.String(150), default='default_user.jpg')
    documento_pdf = db.Column(db.String(150))
    perfil_completo = db.Column(db.Boolean, default=False)
    conta_validada = db.Column(db.Boolean, default=False, index=True)

    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id'))
    municipio_id = db.Column(db.Integer, db.ForeignKey('municipios.id'))
    data_cadastro = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    provincia = db.relationship('Provincia', backref='usuarios')
    municipio = db.relationship('Municipio', backref='usuarios')
    saldo_disponivel = db.Column(db.Numeric(14, 2), default=0.00)


    # Relacionamentos de alta performance

    safras = db.relationship('Safra', back_populates='produtor', lazy='select')
    compras = db.relationship('Transacao', foreign_keys='Transacao.comprador_id', back_populates='comprador',
                              lazy='dynamic')
    vendas = db.relationship('Transacao', foreign_keys='Transacao.vendedor_id', back_populates='vendedor',
                             lazy='dynamic')
    notificacoes = db.relationship('Notificacao', back_populates='usuario', cascade="all, delete-orphan",
                                   lazy='dynamic')


    @property
    def senha(self):
        raise AttributeError('Acesso restrito.')

    @senha.setter
    def senha(self, password):
        self.senha_hash = generate_password_hash(password)

    def verificar_senha(self, password):
        return check_password_hash(self.senha_hash, password)

    def verificar_e_atualizar_perfil(self):
        """
        Valida se os dados obrigatórios de KYC foram preenchidos.
        Retorna True se os dados mínimos para operação existirem.
        """
        try:
            # Campos obrigatórios para todos
            campos_comuns = [self.nome, self.nif, self.provincia_id, self.municipio_id]

            if not all(campos_comuns):
                return False

            # Se for produtor, o IBAN é obrigatório para receber pagamentos
            if self.tipo == 'produtor' and not self.iban:
                return False

            # Se chegou aqui, os dados básicos estão preenchidos
            # O status 'perfil_completo' pode ser usado para libertar o Dashboard
            self.perfil_completo = True
            return True

        except Exception as e:
            # O logger no main.py capturará isto
            raise e



    @validates('telemovel')
    def validate_telemovel(self, key, telemovel):
        num = re.sub(r'\D', '', str(telemovel)) # str() previne erro se for None
        if num.startswith('244'): num = num[3:]
        # Validação simples para números angolanos (9xxxxxxxx)
        # Se vazio (durante o registo inicial), permite passar (será validado na API)
        if not num: return None
        if not re.match(r'^9\d{8}$', num): raise ValueError("Formato AO inválido.")
        return num

    def notificacoes_nao_lidas(self):
        """Retorna a contagem de notificações não lidas para o utilizador."""
        return self.notificacoes.filter_by(lida=False).count()

    def ultimas_notificacoes(self, limite=5):
        return self.notificacoes.order_by(Notificacao.data_criacao.desc()).limit(limite).all()
        
    def __repr__(self):
        return f'<Usuario {self.nome}>'
        
    def to_dict(self):
        """Serialização segura para API."""
        return {
            'id': self.id,
            'nome': self.nome,
            'telemovel': self.telemovel,
            'email': self.email,
            'tipo': self.tipo,
            'nif': self.nif,
            'iban': self.iban,
            'rating': float(self.rating_vendedor),
            'vendas_concluidas': self.vendas_concluidas,
            'foto_perfil': f"/uploads/perfil/{self.foto_perfil}" if self.foto_perfil else None,
            'perfil_completo': self.perfil_completo,
            'conta_validada': self.conta_validada,
            'saldo_disponivel': float(self.saldo_disponivel) if self.tipo == 'produtor' else 0.0,
            'provincia': self.provincia.nome if self.provincia else None,
            'municipio': self.municipio.nome if self.municipio else None
        }



# --- PRODUTOS E SAFRAS ---
class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    categoria = db.Column(db.String(50), index=True)
    
    def __repr__(self):
        return f'<Produto {self.nome}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'categoria': self.categoria
        }


class Safra(db.Model):
    __tablename__ = 'safras'
    __table_args__ = (
        CheckConstraint('quantidade_disponivel >= 0', name='ck_stock_pos'),
        CheckConstraint('preco_por_unidade > 0', name='ck_preco_pos'),
        Index('idx_safra_prod_status', 'produto_id', 'status'),  # Otimiza a vitrine
    )
    id = db.Column(db.Integer, primary_key=True)
    produtor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade_disponivel = db.Column(db.Numeric(12, 2), nullable=False)
    preco_por_unidade = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), default='disponivel', index=True)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    imagem = db.Column(db.String(150), default='default_safra.webp')
    observacoes = db.Column(db.Text)

    produtor = db.relationship('Usuario', back_populates='safras')
    produto = db.relationship('Produto', backref='safras_rel')
    
    def __repr__(self):
        return f'<Safra {self.id} - {self.status}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'produto': self.produto.nome,
            'categoria': self.produto.categoria,
            'quantidade': float(self.quantidade_disponivel),
            'preco': float(self.preco_por_unidade),
            'status': self.status,
            'data_criacao': self.data_criacao.isoformat(),
            'imagem_url': f"/uploads/safras/{self.imagem}" if self.imagem else None,
            'observacoes': self.observacoes,
            'produtor': {
                'id': self.produtor.id,
                'nome': self.produtor.nome,
                'rating': float(self.produtor.rating_vendedor),
                'localizacao': f"{self.produtor.municipio.nome}, {self.produtor.provincia.nome}" if self.produtor.municipio else "Localização N/D"
            }
        }


# --- SISTEMA TRANSACIONAL (O MOTOR) ---
class Transacao(db.Model):
    __tablename__ = 'transacoes'
    __table_args__ = (
        CheckConstraint('comprador_id != vendedor_id', name='ck_no_self_deal'),
        CheckConstraint('valor_total_pago > 0', name='ck_total_pos'),
    )
    id = db.Column(db.Integer, primary_key=True)
    fatura_ref = db.Column(db.String(50), unique=True, nullable=False, index=True)

    safra_id = db.Column(db.Integer, db.ForeignKey('safras.id'), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    quantidade_comprada = db.Column(db.Numeric(12, 2), nullable=False)
    valor_total_pago = db.Column(db.Numeric(14, 2), nullable=False)
    comissao_plataforma = db.Column(db.Numeric(14, 2), default=0.00)
    valor_liquido_vendedor = db.Column(db.Numeric(14, 2), default=0.00)

    status = db.Column(db.String(30), default=TransactionStatus.PENDENTE, index=True)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    data_pagamento_escrow = db.Column(db.DateTime(timezone=True))
    data_envio = db.Column(db.DateTime(timezone=True))
    data_entrega = db.Column(db.DateTime(timezone=True))
    data_liquidacao = db.Column(db.DateTime(timezone=True))
    previsao_entrega = db.Column(db.DateTime(timezone=True))

    comprovativo_path = db.Column(db.String(255))
    transferencia_concluida = db.Column(db.Boolean, default=False)

    comprador = db.relationship('Usuario', foreign_keys=[comprador_id], back_populates='compras')
    vendedor = db.relationship('Usuario', foreign_keys=[vendedor_id], back_populates='vendas')
    safra = db.relationship('Safra', backref='transacoes')
    
    # Relação com logs de status
    historico_status = db.relationship('HistoricoStatus', back_populates='transacao', cascade="all, delete-orphan", lazy='dynamic')
    mensagens = db.relationship('Mensagem', back_populates='transacao', cascade="all, delete-orphan", lazy='dynamic')

    def calcular_janela_logistica(self):
        """Define a previsão de entrega baseada na data de envio (ex: +3 dias)."""
        if self.data_envio:
            # Em Angola, considerando a logística inter-provincial, 3-5 dias é um padrão seguro
            self.previsao_entrega = self.data_envio + timedelta(days=3)

    def __init__(self, **kwargs):
        # Gera referência única se não existir
        if 'fatura_ref' not in kwargs:
            kwargs['fatura_ref'] = f"AK-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
            
        super().__init__(**kwargs)
        self.recalcular_financeiro()

    def recalcular_financeiro(self):
        """Calcula a divisão 95/5 de forma precisa."""
        if self.valor_total_pago:
            # Garante que usamos Decimal para evitar erros de ponto flutuante
            if not isinstance(self.valor_total_pago, Decimal):
                total = Decimal(str(self.valor_total_pago))
            else:
                total = self.valor_total_pago
                
            taxa = Decimal('0.05') # 5%
            self.comissao_plataforma = (total * taxa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.valor_liquido_vendedor = (total - self.comissao_plataforma).quantize(Decimal('0.01'),
                                                                                      rounding=ROUND_HALF_UP)
                                                                                      
    def mudar_status(self, novo_status, observacao=None, usuario=None):
        """Método seguro para mudar status e registar histórico."""
        if self.status != novo_status:
            historico = HistoricoStatus(
                transacao_id=self.id,
                status_anterior=self.status,
                status_novo=novo_status,
                observacao=observacao
            )
            self.status = novo_status
            return historico
        return None

    def __repr__(self):
        return f'<Transacao {self.fatura_ref}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'ref': self.fatura_ref,
            'produto': self.safra.produto.nome,
            'safra_id': self.safra_id,
            'quantidade': float(self.quantidade_comprada),
            'valor_total': float(self.valor_total_pago),
            'status': self.status,
            'data_criacao': self.data_criacao.isoformat(),
            'comprador': self.comprador.nome,
            'vendedor': self.vendedor.nome,
            'previsao_entrega': self.previsao_entrega.strftime('%d/%m/%Y') if self.previsao_entrega else None
        }


# --- APOIO, AUDITORIA E COMUNICAÇÃO ---
class HistoricoStatus(db.Model):
    __tablename__ = 'historico_status'
    id = db.Column(db.Integer, primary_key=True)
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacoes.id', ondelete='CASCADE'), nullable=False)
    status_anterior = db.Column(db.String(30))
    status_novo = db.Column(db.String(30))
    data_mudanca = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    observacao = db.Column(db.String(255))
    
    transacao = db.relationship('Transacao', back_populates='historico_status')


class Notificacao(db.Model):
    __tablename__ = 'notificacoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    mensagem = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255))
    lida = db.Column(db.Boolean, default=False, index=True)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    
    usuario = db.relationship('Usuario', back_populates='notificacoes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'mensagem': self.mensagem,
            'link': self.link,
            'lida': self.lida,
            'data': self.data_criacao.isoformat()
        }


class Mensagem(db.Model):
    __tablename__ = 'mensagens'
    id = db.Column(db.Integer, primary_key=True)
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacoes.id'))
    remetente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_envio = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    lida = db.Column(db.Boolean, default=False)
    
    transacao = db.relationship('Transacao', back_populates='mensagens')
    remetente = db.relationship('Usuario', foreign_keys=[remetente_id])
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'de': self.remetente.nome,
            'de_id': self.remetente_id,
            'para': self.destinatario.nome,
            'conteudo': self.conteudo,
            'data': self.data_envio.isoformat(),
            'lida': self.lida
        }


class Avaliacao(db.Model):
    __tablename__ = 'avaliacoes'
    id = db.Column(db.Integer, primary_key=True)
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacoes.id', ondelete='CASCADE'), nullable=False)
    nota = db.Column(db.Integer, nullable=False)  # 1-5
    comentario = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
    transacao = db.relationship('Transacao', backref=backref('avaliacao', uselist=False))


class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'))
    acao = db.Column(db.String(100), nullable=False)
    detalhes = db.Column(db.Text)
    ip = db.Column(db.String(45))
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)


class AlertaPreferencia(db.Model):
    __tablename__ = 'alertas_preferencias'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    data_criacao = db.Column(db.DateTime(timezone=True), default=aware_utcnow)
