# tests/conftest.py - Configuração de fixtures e ambiente de testes
# Setup completo para testes unitários com banco de dados em memória

import pytest
import tempfile
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app import create_app, db
from app.models import (
    Usuario, Safra, Produto, Provincia, Municipio, 
    Transacao, TransactionStatus, Notificacao
)
from app.models import Disputa
from app.models import StatusConta


@pytest.fixture(scope='session')
def app():
    """Cria aplicação Flask para testes com banco em memória"""
    # Criar banco temporário
    db_fd, db_path = tempfile.mkstemp()
    
    # Configuração de testes
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'UPLOAD_FOLDER_PRIVATE': tempfile.mkdtemp(),
        'UPLOAD_FOLDER_PUBLIC': tempfile.mkdtemp(),
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'memory://'
    }
    
    app = create_app(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Limpeza
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='function')
def client(app):
    """Cliente de teste para requisições HTTP"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Runner para comandos CLI"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def session(app):
    """Sessão de banco de dados isolada para cada teste"""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Usar sessão isolada
        session = db.session(bind=connection)
        
        yield session
        
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def admin_user(session):
    """Usuário admin para testes"""
    admin = Usuario(
        nome="Admin Test",
        telemovel="923456789",
        email="admin@test.com",
        senha="123456",
        tipo="admin",
        conta_validada=True,
        perfil_completo=True,
        status_conta=StatusConta.VERIFICADO
    )
    session.add(admin)
    session.commit()
    return admin


@pytest.fixture
def produtor_user(session):
    """Usuário produtor para testes"""
    produtor = Usuario(
        nome="Produtor Test",
        telemovel="923456788",
        email="produtor@test.com",
        senha="123456",
        tipo="produtor",
        conta_validada=True,
        perfil_completo=True,
        iban="AO0600600000123456789012345",
        status_conta=StatusConta.VERIFICADO
    )
    session.add(produtor)
    session.commit()
    return produtor


@pytest.fixture
def comprador_user(session):
    """Usuário comprador para testes"""
    comprador = Usuario(
        nome="Comprador Test",
        telemovel="923456787",
        email="comprador@test.com",
        senha="123456",
        tipo="comprador",
        conta_validada=True,
        perfil_completo=True,
        status_conta=StatusConta.VERIFICADO
    )
    session.add(comprador)
    session.commit()
    return comprador


@pytest.fixture
def provincia(session):
    """Província para testes"""
    prov = Provincia(nome="Luanda")
    session.add(prov)
    session.commit()
    return prov


@pytest.fixture
def municipio(session, provincia):
    """Município para testes"""
    mun = Municipio(nome="Luanda", provincia_id=provincia.id)
    session.add(mun)
    session.commit()
    return mun


@pytest.fixture
def produto(session):
    """Produto para testes"""
    prod = Produto(nome="Milho", categoria="Cereais")
    session.add(prod)
    session.commit()
    return prod


@pytest.fixture
def safra_ativa(session, produtor_user, produto):
    """Safra ativa para testes"""
    safra = Safra(
        produtor_id=produtor_user.id,
        produto_id=produto.id,
        quantidade_disponivel=Decimal('100.50'),
        preco_por_unidade=Decimal('1500.75'),
        status='disponivel',
        observacoes="Safra de teste"
    )
    session.add(safra)
    session.commit()
    return safra


@pytest.fixture
def transacao_pendente(session, safra_ativa, comprador_user, produtor_user):
    """Transação pendente para testes"""
    transacao = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('10.00'),
        valor_total_pago=Decimal('15007.50'),
        status=TransactionStatus.PENDENTE
    )
    session.add(transacao)
    session.commit()
    return transacao


@pytest.fixture
def transacao_enviada(session, safra_ativa, comprador_user, produtor_user):
    """Transação enviada para testes de disputas"""
    transacao = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('5.00'),
        valor_total_pago=Decimal('7503.75'),
        status=TransactionStatus.ENVIADO,
        data_envio=datetime.now(timezone.utc) - timedelta(hours=48),  # 48h atrás
        previsao_entrega=datetime.now(timezone.utc) - timedelta(hours=24)  # 24h atrás
    )
    session.add(transacao)
    session.commit()
    return transacao


@pytest.fixture
def disputa_aberta(session, transacao_enviada, comprador_user):
    """Disputa aberta para testes"""
    disputa = Disputa(
        transacao_id=transacao_enviada.id,
        comprador_id=comprador_user.id,
        motivo="Produto não entregue na data prevista",
        status='aberta'
    )
    session.add(disputa)
    session.commit()
    return disputa


# Helper functions para testes
@pytest.fixture
def login_comprador(client, comprador_user):
    """Helper para login de comprador"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(comprador_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def login_produtor(client, produtor_user):
    """Helper para login de produtor"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(produtor_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def login_admin(client, admin_user):
    """Helper para login de admin"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client


# Mocks para serviços externos
@pytest.fixture
def mock_celery(monkeypatch):
    """Mock do Celery para testes"""
    class MockTask:
        def __init__(self):
            self.delay_called = False
            self.args = []
        
        def delay(self, *args):
            self.delay_called = True
            self.args = args
            return MockResult()
    
    class MockResult:
        def __init__(self):
            self.id = 'mock-task-id'
            self.status = 'SUCCESS'
    
    mock_task = MockTask()
    monkeypatch.setattr('app.tasks.pagamentos.processar_liquidacao', mock_task)
    monkeypatch.setattr('app.tasks.notificacoes_disputas.enviar_notificacao_disputa_async', mock_task)
    
    return mock_task
