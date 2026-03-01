# tests_framework/conftest_fixed.py - Configuração completa de testes corrigida
# Versão corrigida sem referências a StatusConta

import pytest
import tempfile
import os
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app import create_app, db
from app.models import (
    Usuario, Safra, Transacao, TransactionStatus,
    Notificacao, Produto, Provincia, Municipio
)
from app.models_carteiras import Carteira


@pytest.fixture(scope='session')
def app():
    """Cria aplicação Flask para testes com banco em memória"""
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
        MAIL_SUPPRESS_SEND=True,
        CELERY_TASK_ALWAYS_EAGER=True
    )
    
    with app.app_context():
        db.create_all()
        yield app


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
    
    # Criar carteira
    carteira = Carteira(usuario_id=produtor.id, saldo_disponivel=Decimal('100000.00'))
    session.add(carteira)
    session.commit()
    
    return produtor


@pytest.fixture
def comprador_user(session, provincia, municipio):
    """Usuário comprador para testes"""
    comprador = Usuario(
        nome="Comprador Test",
        telemovel="923456789",
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
def admin_user(session, provincia, municipio):
    """Usuário admin para testes"""
    admin = Usuario(
        nome="Admin Test",
        telemovel="923456789",
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


@pytest.fixture(autouse=True)
def cleanup_session(session):
    """Limpa sessão após cada teste"""
    yield
    session.remove()
    db.drop_all()


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
