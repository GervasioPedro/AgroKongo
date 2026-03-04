"""
Modelos consolidados do AgroKongo
Importar deste módulo: from app.models import Usuario, Transacao, etc.
"""

# Base
from app.models.base import aware_utcnow, TransactionStatus, StatusConta

# Usuário e Localização
from app.models.usuario import Usuario, Provincia, Municipio

# Produto e Safra
from app.models.produto import Produto, Safra

# Transação
from app.models.transacao import Transacao, HistoricoStatus

# Avaliação
from app.models.avaliacao import Avaliacao # <-- ADICIONADO

# Financeiro
from app.models.financeiro import Carteira, MovimentacaoFinanceira

# Notificação
from app.models.notificacao import Notificacao, AlertaPreferencia

# Disputa
from app.models.disputa import Disputa

# Auditoria
from app.models.auditoria import LogAuditoria, ConfiguracaoSistema

# LGPD - Conformidade com Lei de Proteção de Dados de Angola
from app.models.lgpd import ConsentimentoLGPD, RegistroAnonimizacao

__all__ = [
    # Base
    'aware_utcnow',
    'TransactionStatus',
    'StatusConta',
    # Usuário
    'Usuario',
    'Provincia',
    'Municipio',
    # Produto
    'Produto',
    'Safra',
    # Transação
    'Transacao',
    'HistoricoStatus',
    # Avaliação
    'Avaliacao', # <-- ADICIONADO
    # Financeiro
    'Carteira',
    'MovimentacaoFinanceira',
    # Notificação
    'Notificacao',
    'AlertaPreferencia',
    # Disputa
    'Disputa',
    # Auditoria
    'LogAuditoria',
    'ConfiguracaoSistema',
    # LGPD
    'ConsentimentoLGPD',
    'RegistroAnonimizacao',
]
