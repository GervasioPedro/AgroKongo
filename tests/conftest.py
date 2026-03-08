# tests/conftest.py - Configuração ROBUSTA v4
import pytest
import tempfile
import os
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta # Import adicionado
from app import create_app, db
from app.models import (
    Usuario, Safra, Produto, Provincia, Municipio, 
    Transacao, TransactionStatus, Notificacao, Disputa
)

@pytest.fixture(scope='function')
def app():
    """
    Cria uma NOVA aplicação Flask para CADA teste.
    """
    db_fd, db_path = tempfile.mkstemp()
    
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key-unique',
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'memory://',
        'SERVER_NAME': 'localhost.test',  # Necessário para url_for fora de requests
        'APPLICATION_ROOT': '/',
        'PREFERRED_URL_SCHEME': 'http',
        'SUBFOLDERS': {
            'faturas': '/tmp/faturas'
        }
    }
    
    # Passar test_config_override para o create_app
    app = create_app('dev', test_config_override=test_config)
    
    # Contexto de aplicação é essencial
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except:
        pass

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def session(app):
    """
    Retorna a sessão do banco de dados.
    O contexto da app já está ativo graças à fixture 'app'.
    """
    with app.app_context():
        yield db.session

# --- Helpers de Dados ---

def gerar_dados_unicos(prefixo):
    uid = str(uuid.uuid4())[:8]
    return {
        'nome': f"{prefixo} {uid}",
        'email': f"{prefixo.lower()}.{uid}@test.com",
        'telemovel': f"9{uid[:8].replace('-', '').replace('a', '1').replace('b', '2').replace('c', '3').replace('d', '4').replace('e', '5').replace('f', '6')[:8]}"
    }

# --- Fixtures de Modelos ---

@pytest.fixture
def admin_user(app, session):
    with app.app_context():
        dados = gerar_dados_unicos("Admin")
        admin = Usuario(
            nome=dados['nome'],
            telemovel=dados['telemovel'],
            email=dados['email'],
            senha="123456",
            tipo="admin",
            conta_validada=True,
            perfil_completo=True
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin

@pytest.fixture
def produtor_user(app, session):
    with app.app_context():
        dados = gerar_dados_unicos("Produtor")
        produtor = Usuario(
            nome=dados['nome'],
            telemovel=dados['telemovel'],
            email=dados['email'],
            senha="123456",
            tipo="produtor",
            conta_validada=True,
            perfil_completo=True,
            iban="AO0600600000123456789012345"
        )
        session.add(produtor)
        session.commit()
        session.refresh(produtor)
        return produtor

@pytest.fixture
def comprador_user(app, session):
    with app.app_context():
        dados = gerar_dados_unicos("Comprador")
        comprador = Usuario(
            nome=dados['nome'],
            telemovel=dados['telemovel'],
            email=dados['email'],
            senha="123456",
            tipo="comprador",
            conta_validada=True,
            perfil_completo=True
        )
        session.add(comprador)
        session.commit()
        session.refresh(comprador)
        return comprador

@pytest.fixture
def outro_usuario(app, session):
    """Segundo usuário para testes de permissão"""
    with app.app_context():
        dados = gerar_dados_unicos("OutroUsuario")
        usuario = Usuario(
            nome=dados['nome'],
            telemovel=dados['telemovel'],
            email=dados['email'],
            senha="123456",
            tipo="comprador",
            conta_validada=True,
            perfil_completo=True
        )
        session.add(usuario)
        session.commit()
        session.refresh(usuario)
        return usuario

@pytest.fixture
def produto(app, session):
    with app.app_context():
        prod = Produto(nome="Milho", categoria="Cereais")
        session.add(prod)
        session.commit()
        session.refresh(prod)
        return prod

@pytest.fixture
def safra_ativa(app, session, produtor_user, produto):
    with app.app_context():
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
        session.refresh(safra)
        return safra

@pytest.fixture
def transacao_enviada(app, session, safra_ativa, comprador_user, produtor_user):
    with app.app_context():
        transacao = Transacao(
            fatura_ref=f"TRX-{uuid.uuid4()}",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('5.00'),
            valor_total_pago=Decimal('7503.75'),
            status=TransactionStatus.ENVIADO,
            data_envio=datetime.now(timezone.utc) - timedelta(hours=48),
            previsao_entrega=datetime.now(timezone.utc) - timedelta(hours=24)
        )
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        return transacao

@pytest.fixture
def transacao_pendente(app, session, safra_ativa, comprador_user, produtor_user):
    with app.app_context():
        transacao = Transacao(
            fatura_ref=f"TRX-{uuid.uuid4()}",
            safra_id=safra_ativa.id,
            comprador_id=comprador_user.id,
            vendedor_id=produtor_user.id,
            quantidade_comprada=Decimal('10.00'),
            valor_total_pago=Decimal('15007.50'),
            status=TransactionStatus.PENDENTE
        )
        session.add(transacao)
        session.commit()
        session.refresh(transacao)
        return transacao

@pytest.fixture
def disputa_aberta(app, session, transacao_enviada, comprador_user):
    with app.app_context():
        disputa = Disputa(
            transacao_id=transacao_enviada.id,
            comprador_id=comprador_user.id,
            motivo="Produto não entregue",
            status='aberta'
        )
        session.add(disputa)
        session.commit()
        session.refresh(disputa)
        return disputa

# --- Auth Helpers ---
@pytest.fixture
def auth_client(client, admin_user):
    """Cliente autenticado como admin"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client

@pytest.fixture
def auth_comprador_client(client, comprador_user):
    """Cliente autenticado como comprador"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(comprador_user.id)
        sess['_fresh'] = True
    return client

@pytest.fixture
def auth_produtor_client(client, produtor_user):
    """Cliente autenticado como produtor"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(produtor_user.id)
        sess['_fresh'] = True
    return client

# --- Mocks ---
@pytest.fixture
def mock_redis(monkeypatch):
    class MockRedis:
        def __init__(self): self.data = {}
        def set(self, k, v, ex=None): self.data[k] = v
        def get(self, k): return self.data.get(k)
        def delete(self, k): self.data.pop(k, None)
        def exists(self, k): return k in self.data
    
    mock = MockRedis()
    monkeypatch.setattr('redis.Redis', lambda *a, **kw: mock)
    return mock

@pytest.fixture
def mock_celery(monkeypatch):
    class MockResult:
        id = 'mock-id'
        status = 'SUCCESS'
    
    class MockTask:
        def delay(self, *args, **kwargs): return MockResult()
        
    mock = MockTask()
    monkeypatch.setattr('app.tasks.pagamentos.processar_liquidacao', mock)
    return mock
