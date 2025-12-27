from extensions import db
from datetime import datetime
from flask_login import UserMixin


# --- LOCALIZAÇÃO ---
class Provincia(db.Model):
    __tablename__ = 'provincias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    municipios = db.relationship('Municipio', backref='provincia_pai', lazy=True, cascade="all, delete-orphan")


class Municipio(db.Model):
    __tablename__ = 'municipios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id'), nullable=False)

    def __repr__(self):
        return self.nome


# --- UTILIZADORES ---
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    telemovel = db.Column(db.String(20), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), default='produtor')  # 'produtor' ou 'comprador'
    nome = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)

    # NOVOS CAMPOS: Identificação e Pagamento
    nif = db.Column(db.String(20), unique=True, nullable=True)
    iban = db.Column(db.String(30), unique=True, nullable=True)  # Essencial para o Produtor

    provincia_id = db.Column(db.Integer, db.ForeignKey('provincias.id'), nullable=True)
    municipio_id = db.Column(db.Integer, db.ForeignKey('municipios.id'), nullable=True)
    referencia = db.Column(db.Text, nullable=True)

    provincia = db.relationship('Provincia', backref='usuarios_na_provincia')
    municipio = db.relationship('Municipio', backref='usuarios_no_municipio')
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def nome_exibicao(self):
        if self.nome:
            return self.nome.split()[0]
        return f"Membro {self.telemovel[-3:]}"

    def obter_reputacao(self):
        avaliacoes = Avaliacao.query.join(Safra).filter(Safra.produtor_id == self.id).all()
        if not avaliacoes:
            return 0.0
        media = sum(a.estrelas for a in avaliacoes) / len(avaliacoes)
        return round(media, 1)


# --- CATÁLOGO ---
class Produto(db.Model):
    __tablename__ = 'produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    categoria = db.Column(db.String(50), nullable=True)


class Safra(db.Model):
    __tablename__ = 'safras'
    id = db.Column(db.Integer, primary_key=True)
    produtor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade_kg = db.Column(db.Float, nullable=False)
    preco_kg = db.Column(db.Float, nullable=False)
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='disponivel')

    produto = db.relationship('Produto', backref='safras_deste_produto')
    produtor = db.relationship('Usuario', backref='minhas_safras')


class Interesse(db.Model):
    __tablename__ = 'interesses'
    id = db.Column(db.Integer, primary_key=True)
    safra_id = db.Column(db.Integer, db.ForeignKey('safras.id'), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    quantidade_pretendida = db.Column(db.Float, nullable=False, default=0.0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')

    safra = db.relationship('Safra', backref='interesses_registados')
    comprador = db.relationship('Usuario', backref='interesses_enviados')


class Transacao(db.Model):
    __tablename__ = 'transacoes'
    id = db.Column(db.Integer, primary_key=True)
    safra_id = db.Column(db.Integer, db.ForeignKey('safras.id'), nullable=False)
    comprador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    quantidade = db.Column(db.Float, nullable=False)
    preco_total = db.Column(db.Float, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    # Estados atualizados para o fluxo profissional:
    # 'pendente_pagamento', 'aguardando_validacao' (para IBAN), 'pago_custodia', 'concluido', 'rejeitado_reembolsado'
    status = db.Column(db.String(30), default='pendente_pagamento')

    # NOVOS CAMPOS: Gestão de Pagamento Angola
    metodo_pagamento = db.Column(db.String(20))  # 'express' ou 'transferencia'
    comprovativo_path = db.Column(db.String(255))  # Caminho do ficheiro do comprovativo IBAN
    fatura_ref = db.Column(db.String(20), unique=True)

    safra = db.relationship('Safra', backref='historico_vendas')
    comprador = db.relationship('Usuario', backref='historico_compras')

    @property
    def produtor(self):
        return self.safra.produtor

    @property
    def avaliado(self):
        return Avaliacao.query.filter_by(safra_id=self.safra_id, autor_id=self.comprador_id).first() is not None


class Avaliacao(db.Model):
    __tablename__ = 'avaliacoes'
    id = db.Column(db.Integer, primary_key=True)
    comentario = db.Column(db.Text, nullable=False)
    estrelas = db.Column(db.Integer, nullable=False)
    safra_id = db.Column(db.Integer, db.ForeignKey('safras.id'), nullable=False)
    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    safra = db.relationship('Safra', backref='avaliacoes')
    autor = db.relationship('Usuario', backref='minhas_avaliacoes')


from datetime import datetime
from extensions import db


class Notificacao(db.Model):
    __tablename__ = 'notificacoes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='info')  # info, success, warning, danger
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    link = db.Column(db.String(255))  # URL para onde o user vai ao clicar (ex: dashboard)

    # Relacionamento
    usuario = db.relationship('Usuario', backref=db.backref('notificacoes', lazy='dynamic'))