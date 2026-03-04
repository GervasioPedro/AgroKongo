"""
Modelo de Consentimento LGPD/LPDP (Lei de Proteção de Dados Pessoais de Angola)
Implementa conformidade com os artigos 8º e 18º da LPDP
"""
from datetime import datetime, timezone
from app.extensions import db


class ConsentimentoLGPD(db.Model):
    """
    Registro de consentimentos do utilizador para processamento de dados pessoais.
    Conforme Art. 8º da LPDP - Consentimento como base legal para tratamento.
    """
    __tablename__ = 'consentimentos_lgpd'

    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamento com utilizador
    usuario_id = db.Column(
        db.Integer, 
        db.ForeignKey('usuarios.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Tipo de consentimento
    tipo = db.Column(
        db.String(50), 
        nullable=False,
        index=True
    )
    # Exemplos: 'termos_uso', 'privacidade', 'marketing', 'dados_financeiros', 'compartilhamento_terceiros'
    
    # Versão do documento aceito (para auditoria)
    versao_documento = db.Column(db.String(20), nullable=False)
    
    # Status do consentimento
    consentido = db.Column(db.Boolean, nullable=False, default=True)
    
    # IP e User Agent no momento do consentimento
    ip_consentimento = db.Column(db.String(45))
    user_agent_consentimento = db.Column(db.String(500))
    
    # Timestamp
    data_consentimento = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    data_revogacao = db.Column(db.DateTime(timezone=True))
    
    # Metadata adicional
    motivo_revogacao = db.Column(db.String(255))
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref=db.backref('consentimentos', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Índices para performance
    __table_args__ = (
        db.Index('idx_consentimento_usuario_tipo', 'usuario_id', 'tipo'),
        db.Index('idx_consentimento_usuario_valido', 'usuario_id', 'consentido'),
    )
    
    def __repr__(self):
        return f'<ConsentimentoLGPD {self.usuario_id} - {self.tipo}>'
    
    def revogar(self, motivo: str = None):
        """Revoga o consentimento dado"""
        self.consentido = False
        self.data_revogacao = datetime.now(timezone.utc)
        self.motivo_revogacao = motivo
    
    @staticmethod
    def verificar_consentimento(usuario_id: int, tipo: str) -> bool:
        """
        Verifica se o utilizador deu consentimento para um tipo específico.
        Retorna False se não existir consentimento ou se foi revogado.
        """
        consentimento = ConsentimentoLGPD.query.filter_by(
            usuario_id=usuario_id,
            tipo=tipo,
            consentido=True
        ).order_by(ConsentimentoLGPD.data_consentimento.desc()).first()
        
        return consentimento is not None
    
    @staticmethod
    def registrar_consentimento(
        usuario_id: int, 
        tipo: str, 
        versao: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> 'ConsentimentoLGPD':
        """
        Registra um novo consentimento ou renova um existente.
        Retorna o objeto ConsentimentoLGPD criado.
        """
        # Revogar consentimentos anteriores do mesmo tipo
        consentimentos_anteriores = ConsentimentoLGPD.query.filter_by(
            usuario_id=usuario_id,
            tipo=tipo,
            consentido=True
        ).all()
        
        for c in consentimentos_anteriores:
            c.revogar('Novo consentimento registrado')
        
        # Criar novo consentimento
        novo_consentimento = ConsentimentoLGPD(
            usuario_id=usuario_id,
            tipo=tipo,
            versao_documento=versao,
            consentido=True,
            ip_consentimento=ip_address,
            user_agent_consentimento=user_agent
        )
        
        db.session.add(novo_consentimento)
        return novo_consentimento


class RegistroAnonimizacao(db.Model):
    """
    Registro de anonimização de dados pessoais.
    Conforme Art. 18º da LPDP - Direito ao Esquecimento.
    """
    __tablename__ = 'registros_anonimizacao'

    id = db.Column(db.Integer, primary_key=True)
    
    usuario_id = db.Column(
        db.Integer, 
        db.ForeignKey('usuarios.id', ondelete='SET NULL'),
        unique=True,
        index=True
    )
    
    # Dados que foram anonimizados
    dados_anonimizados = db.Column(db.JSON)  # Lista de campos anonimizados
    
    # Hash para identificação sem expor ID do utilizador
    hash_anonimizacao = db.Column(db.String(64), unique=True, index=True)
    
    # Timestamp
    data_anonimizacao = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Motivo da anonimização
    motivo = db.Column(db.String(255))  # 'solicitacao_usuario', 'inatividade', etc.
    
    # Quem solicitou
    solicitado_por = db.Column(db.String(50))  # 'usuario', 'admin', 'sistema'
    
    def __repr__(self):
        return f'<RegistroAnonimizacao {self.usuario_id} - {self.hash_anonimizacao[:8]}...>'
