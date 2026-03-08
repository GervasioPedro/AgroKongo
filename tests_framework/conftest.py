# tests_framework/conftest.py - Configuração corporativa de testes
# Versão profissional com todos os modelos importados explicitamente

import os
import sys
from pathlib import Path

# Adicionar root do projeto ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import pytest
import tempfile
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app import create_app
from app.extensions import db

# IMPORTAR TODOS OS MODELOS EXPLICITAMENTE ANTES DE CRIAR TABELAS
# Isso garante que o SQLAlchemy registre todos os modelos antes do db.create_all()
from app.models import (
    Usuario,
    Provincia,
    Municipio,
    Produto,
    Safra,
    Transacao,
    HistoricoStatus,
    TransactionStatus,
    Avaliacao,
    Notificacao,
    AlertaPreferencia,
    Disputa,
    LogAuditoria,
    ConfiguracaoSistema,
    ConsentimentoLGPD,
    RegistroAnonimizacao,
)
from app.models.financeiro import Carteira, MovimentacaoFinanceira


@pytest.fixture(scope='session')
def app():
    """Cria aplicação Flask para testes com banco em memória"""
    # Definir variável de ambiente ANTES de criar o app
    os.environ['TEST_DATABASE_URL'] = 'sqlite:///:memory:'
    
    app = create_app('dev')  # Criar com config de desenvolvimento
    
    # Sobrescrever configurações para testes
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
        MAIL_SUPPRESS_SEND=True,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_BROKER_URL='memory://'
    )
    
    with app.app_context():
        # CRÍTICO: Importar todos os modelos para registrar no metadata do SQLAlchemy
        from app.models import (
            Usuario, Provincia, Municipio, Produto, Safra,
            Transacao, HistoricoStatus, Avaliacao, Notificacao,
            AlertaPreferencia, Disputa, LogAuditoria, ConfiguracaoSistema,
            ConsentimentoLGPD, RegistroAnonimizacao,
        )
        from app.models.financeiro import Carteira, MovimentacaoFinanceira
        
        # Usar db.create_all() que é o método correto para Flask-SQLAlchemy
        # Isso cria todas as tabelas registradas no metadata
        db.create_all()
        
        yield app
        
        # Cleanup no final da sessão de testes
        db.drop_all()


@pytest.fixture(scope='session')
def session(app):
    """Sessão do banco de dados para testes"""
    return db.session


@pytest.fixture(scope='session')
def client(app):
    """Cliente de teste para fazer requisições HTTP"""
    return app.test_client()


@pytest.fixture(scope='session')
def runner(app):
    """Runner de teste para comandos CLI"""
    return app.test_cli_runner()


@pytest.fixture
def mock_celery():
    """Mock do Celery para testes"""
    from unittest.mock import MagicMock
    celery = MagicMock()
    celery.Task = MagicMock()
    return celery


@pytest.fixture
def mock_redis():
    """Mock do Redis para testes"""
    from unittest.mock import MagicMock
    redis = MagicMock()
    redis.ping.return_value = True
    return redis


@pytest.fixture
def provincia(session):
    """Província para testes"""
    provincia = Provincia(nome="Luanda")
    session.add(provincia)
    session.commit()
    return provincia


@pytest.fixture
def municipio(session, provincia):
    """Município para testes"""
    municipio = Municipio(nome="Luanda", provincia_id=provincia.id)
    session.add(municipio)
    session.commit()
    return municipio


@pytest.fixture
def produtor_user(session, provincia, municipio):
    """Usuário produtor para testes"""
    produtor = Usuario(
        nome="Produtor Test",
        telemovel="923456788",
        email="produtor@test.com",
        senha="123456",
        tipo="produtor",
        conta_validada=True,
        perfil_completo=True,
        provincia_id=provincia.id,
        municipio_id=municipio.id
    )
    session.add(produtor)
    session.commit()
    
    # Criar carteira com saldo ZERO (para testes de débito/bloqueio)
    carteira = Carteira(usuario_id=produtor.id, saldo_disponivel=Decimal('0.00'))
    session.add(carteira)
    session.commit()
    
    return produtor


@pytest.fixture
def comprador_user(session, provincia, municipio):
    """Usuário comprador para testes"""
    comprador = Usuario(
        nome="Comprador Test",
        telemovel="923456790",  # Alterado para evitar conflito
        email="comprador@test.com",
        senha="123456",
        tipo="comprador",
        conta_validada=True,
        perfil_completo=True,
        provincia_id=provincia.id,
        municipio_id=municipio.id
    )
    session.add(comprador)
    session.commit()
    
    # Criar carteira com saldo
    carteira = Carteira(usuario_id=comprador.id, saldo_disponivel=Decimal('100000.00'))
    session.add(carteira)
    session.commit()
    
    return comprador


@pytest.fixture
def safra_ativa(session, produtor_user):
    """Safra ativa para testes"""
    produto = Produto(nome="Milho", categoria="Grãos")
    session.add(produto)
    session.commit()
    
    safra = Safra(
        produtor_id=produtor_user.id,
        produto_id=produto.id,
        quantidade_disponivel=Decimal('1000.00'),
        preco_por_unidade=Decimal('150.00'),
        status='disponivel'
    )
    session.add(safra)
    session.commit()
    return safra


@pytest.fixture
def produto(session):
    """Produto para testes"""
    produto = Produto(nome="Milho", categoria="Grãos")
    session.add(produto)
    session.commit()
    return produto


@pytest.fixture
def transacao_pendente(session, safra_ativa, comprador_user, produtor_user):
    """Transação pendente para testes"""
    transacao = Transacao(
        fatura_ref=f"AGK{datetime.now().strftime('%Y%m%d%H%M%S')}",
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('100.00'),
        valor_total_pago=Decimal('15000.00'),
        status=TransactionStatus.PENDENTE
    )
    transacao.recalcular_financeiro()
    session.add(transacao)
    session.commit()
    return transacao


@pytest.fixture
def transacao_escrow(session, safra_ativa, comprador_user, produtor_user):
    """Transação em escrow para testes"""
    transacao = Transacao(
        fatura_ref=f"AGK{datetime.now().strftime('%Y%m%d%H%M%S')}",
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('100.00'),
        valor_total_pago=Decimal('15000.00'),
        status=TransactionStatus.ESCROW,
        data_pagamento_escrow=datetime.now(timezone.utc)
    )
    transacao.recalcular_financeiro()
    session.add(transacao)
    session.commit()
    return transacao


@pytest.fixture
def transacao_finalizada(session, safra_ativa, comprador_user, produtor_user):
    """Transação finalizada para testes"""
    transacao = Transacao(
        fatura_ref=f"AGK{datetime.now().strftime('%Y%m%d%H%M%S')}",
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('100.00'),
        valor_total_pago=Decimal('15000.00'),
        status=TransactionStatus.FINALIZADO,
        data_liquidacao=datetime.now(timezone.utc),
        transferencia_concluida=True
    )
    transacao.recalcular_financeiro()
    session.add(transacao)
    session.commit()
    return transacao


@pytest.fixture
def disputa_ativa(session, transacao_escrow, comprador_user):
    """Disputa ativa para testes"""
    from app.models.disputa import Disputa
    disputa = Disputa(
        transacao_id=transacao_escrow.id,
        comprador_id=comprador_user.id,
        motivo="Produto não conforme",
        status="aberta"
    )
    session.add(disputa)
    session.commit()
    return disputa


@pytest.fixture
def admin_user(session, provincia, municipio):
    """Usuário admin para testes"""
    admin = Usuario(
        nome="Admin Test",
        telemovel="923456791",  # Alterado para evitar conflito
        email="admin@test.com",
        senha="123456",
        tipo="admin",
        conta_validada=True,
        perfil_completo=True,
        provincia_id=provincia.id,
        municipio_id=municipio.id
    )
    session.add(admin)
    session.commit()
    return admin


# Fixture de cleanup para limpar dados após cada teste
@pytest.fixture(autouse=True)
def cleanup_data(session):
    """Limpa dados criados durante o teste, mantendo estrutura do banco"""
    yield
    # Rollback para desfazer quaisquer mudanças pendentes
    session.rollback()
    # Remover todos os dados criados durante o teste
    try:
        # Ordem inversa de dependência
        from app.models.financeiro import Carteira, MovimentacaoFinanceira
        from app.models import (
            Usuario, Provincia, Municipio, Produto, Safra,
            Transacao, HistoricoStatus, Avaliacao, Notificacao,
            AlertaPreferencia, Disputa, LogAuditoria, ConfiguracaoSistema,
            ConsentimentoLGPD, RegistroAnonimizacao,
        )
        
        # Deletar em ordem correta (filhos primeiro)
        for model in [MovimentacaoFinanceira, Carteira, Notificacao, HistoricoStatus, 
                      Transacao, Safra, Produto, Avaliacao, AlertaPreferencia, 
                      Disputa, LogAuditoria, ConsentimentoLGPD, RegistroAnonimizacao,
                      ConfiguracaoSistema, Usuario, Municipio, Provincia]:
            try:
                session.query(model).delete()
            except Exception:
                pass  # Tabela pode não existir ou não ter dados
        
        session.commit()
    except Exception:
        session.rollback()


# Marcadores personalizados para organização
def pytest_configure(config):
    config.addinivalue_line(
        "markers", [
            "unit: Testes unitários isolados",
            "integration: Testes de integração entre componentes",
            "e2e: Testes end-to-end completos",
            "financial: Testes relacionados a fluxos financeiros",
            "security: Testes de segurança e validações",
            "performance: Testes de performance e carga",
            "slow: Testes lentos que requerem mais tempo",
            "database: Testes que requerem acesso ao banco de dados",
            "api: Testes de endpoints da API",
            "celery: Testes relacionados a tarefas Celery"
        ]
    )
