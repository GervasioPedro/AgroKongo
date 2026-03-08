# tests/integration/conftest_integration.py - Configuração adicional para testes de integração
# Setup específico para testes que envolvem múltiplos componentes

import pytest
import tempfile
import os
from unittest.mock import MagicMock
from decimal import Decimal
from datetime import datetime, timezone, timedelta

from app import create_app, db
from app.models import (
    Usuario, Safra, Produto, Provincia, Municipio,
    Transacao, TransactionStatus, Notificacao
)
from app.models import Disputa


@pytest.fixture(scope='session')
def app_integration():
    """Aplicação configurada para testes de integração"""
    # Configuração mais próxima da produção
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # Em memória para velocidade
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'integration-test-secret',
        'UPLOAD_FOLDER_PRIVATE': tempfile.mkdtemp(),
        'UPLOAD_FOLDER_PUBLIC': tempfile.mkdtemp(),
        
        # Configuração Celery para testes
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'memory://',
        'CELERY_TASK_ALWAYS_EAGER': True,  # Executar tasks sincronamente para testes
        'CELERY_TASK_EAGER_PROPAGATES': True,
        
        # Configurações de performance para testes
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        },
        
        # Logging para debug
        'LOG_LEVEL': 'DEBUG'
    }
    
    # Criar app com configurações de teste aplicadas desde o início
    app = create_app('dev', test_config_override=test_config)
    
    # Configurar extensões manualmente para testes
    with app.app_context():
        # Inicializar SQLAlchemy
        from app.extensions import db
        db.init_app(app)
        
        # Inicializar outras extensões
        from flask_migrate import Migrate
        from flask_wtf import CSRFProtect
        from flask_login import LoginManager
        from flask_mail import Mail
        from flask_limiter import Limiter
        from flask_caching import Cache
        from flask_cors import CORS
        
        migrate = Migrate()
        migrate.init_app(app, db)
        
        csrf = CSRFProtect()
        csrf.init_app(app)
        
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.session_protection = "strong"
        login_manager.login_view = 'auth.login'
        
        mail = Mail()
        mail.init_app(app)
        
        limiter = Limiter(key_func=lambda: 'test', default_limits=["200 per day", "50 per hour"])
        limiter.init_app(app)
        limiter.enabled = False
        
        cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
        cache.init_app(app)
        
        CORS(app)
        
        # Configurar Celery para testes (síncrono)
        from app.tasks import make_celery
        if make_celery:
            celery = make_celery(app)
            celery.conf.update(
                task_always_eager=True,
                task_eager_propagates=True,
                broker_url='memory://',
                result_backend='memory://'
            )
            app.celery = celery
        
        # Criar tabelas
        db.create_all()
        yield app
        db.drop_all()
    
    # Limpeza
    import shutil
    shutil.rmtree(test_config['UPLOAD_FOLDER_PRIVATE'], ignore_errors=True)
    shutil.rmtree(test_config['UPLOAD_FOLDER_PUBLIC'], ignore_errors=True)


@pytest.fixture(scope='function')
def session_integration(app_integration):
    """Sessão de banco com configurações de integração"""
    with app_integration.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        session = db.session(bind=connection)
        
        yield session
        
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def massa_dados_transacoes(session_integration, safra_ativa, comprador_user, produtor_user):
    """Cria massa de dados para testes de performance"""
    transacoes = []
    
    # Criar transações em diferentes estados
    estados_quantidades = {
        TransactionStatus.PENDENTE: 5,
        TransactionStatus.ANALISE: 3,
        TransactionStatus.ESCROW: 4,
        TransactionStatus.ENVIADO: 6,
        TransactionStatus.ENTREGUE: 7,
        TransactionStatus.FINALIZADO: 10,
        TransactionStatus.CANCELADO: 2
    }
    
    for estado, quantidade in estados_quantidades.items():
        for i in range(quantidade):
            transacao = Transacao(
                safra_id=safra_ativa.id,
                comprador_id=comprador_user.id,
                vendedor_id=produtor_user.id,
                quantidade_comprada=Decimal('1.00'),
                valor_total_pago=Decimal('1500.75'),
                status=estado
            )
            
            # Adicionar timestamps apropriados
            if estado == TransactionStatus.ANALISE:
                transacao.comprovativo_path = f'comprovativo_{i}.pdf'
            elif estado == TransactionStatus.ESCROW:
                transacao.data_pagamento_escrow = datetime.now(timezone.utc) - timedelta(hours=i)
            elif estado == TransactionStatus.ENVIADO:
                transacao.data_envio = datetime.now(timezone.utc) - timedelta(hours=i*2)
                transacao.calcular_janela_logistica()
            elif estado == TransactionStatus.ENTREGUE:
                transacao.data_envio = datetime.now(timezone.utc) - timedelta(hours=i*3)
                transacao.data_entrega = datetime.now(timezone.utc) - timedelta(hours=i)
                transacao.calcular_janela_logistica()
            elif estado == TransactionStatus.FINALIZADO:
                transacao.data_envio = datetime.now(timezone.utc) - timedelta(hours=i*4)
                transacao.data_entrega = datetime.now(timezone.utc) - timedelta(hours=i*3)
                transacao.data_liquidacao = datetime.now(timezone.utc) - timedelta(hours=i*2)
                transacao.transferencia_concluida = True
                transacao.calcular_janela_logistica()
            elif estado == TransactionStatus.CANCELADO:
                transacao.data_criacao = datetime.now(timezone.utc) - timedelta(days=i+1)
            
            transacoes.append(transacao)
            session_integration.add(transacao)
    
    session_integration.commit()
    
    return {
        'transacoes': transacoes,
        'totais': {estado: len([t for t in transacoes if t.status == estado]) 
                  for estado in estados_quantidades}
    }


@pytest.fixture
def cenario_escrow_completo(session_integration, safra_ativa, comprador_user, produtor_user):
    """Cria cenário completo de escrow para testes"""
    # Criar transação em cada estado do fluxo
    fluxo_transacoes = {}
    
    # 1. PENDENTE
    fluxo_transacoes['pendente'] = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('5.00'),
        valor_total_pago=Decimal('7503.75'),
        status=TransactionStatus.PENDENTE
    )
    
    # 2. ANALISE
    fluxo_transacoes['analise'] = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('3.00'),
        valor_total_pago=Decimal('4502.25'),
        status=TransactionStatus.ANALISE,
        comprovativo_path='comprovativo.pdf'
    )
    
    # 3. ESCROW
    fluxo_transacoes['escrow'] = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('4.00'),
        valor_total_pago=Decimal('6003.00'),
        status=TransactionStatus.ESCROW,
        data_pagamento_escrow=datetime.now(timezone.utc) - timedelta(hours=2)
    )
    
    # 4. ENVIADO
    fluxo_transacoes['enviado'] = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('2.00'),
        valor_total_pago=Decimal('3001.50'),
        status=TransactionStatus.ENVIADO,
        data_envio=datetime.now(timezone.utc) - timedelta(hours=6)
    )
    fluxo_transacoes['enviado'].calcular_janela_logistica()
    
    # 5. ENTREGUE
    fluxo_transacoes['entregue'] = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('6.00'),
        valor_total_pago=Decimal('9004.50'),
        status=TransactionStatus.ENTREGUE,
        data_envio=datetime.now(timezone.utc) - timedelta(hours=12),
        data_entrega=datetime.now(timezone.utc) - timedelta(hours=6)
    )
    fluxo_transacoes['entregue'].calcular_janela_logistica()
    
    # 6. FINALIZADO
    fluxo_transacoes['finalizado'] = Transacao(
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('7.00'),
        valor_total_pago=Decimal('10505.25'),
        status=TransactionStatus.FINALIZADO,
        data_envio=datetime.now(timezone.utc) - timedelta(hours=24),
        data_entrega=datetime.now(timezone.utc) - timedelta(hours=18),
        data_liquidacao=datetime.now(timezone.utc) - timedelta(hours=12),
        transferencia_concluida=True
    )
    fluxo_transacoes['finalizado'].calcular_janela_logistica()
    
    # Salvar todas
    for transacao in fluxo_transacoes.values():
        session_integration.add(transacao)
    
    session_integration.commit()
    
    return fluxo_transacoes


@pytest.fixture
def mock_redis():
    """Mock do Redis para testes de Celery"""
    mock_redis = MagicMock()
    
    # Simular operações básicas do Redis
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    
    return mock_redis


@pytest.fixture
def performance_monitor():
    """Monitor de performance para testes"""
    import time
    import psutil
    import os
    
    class PerformanceMonitor:
        def __init__(self):
            self.process = psutil.Process(os.getpid())
            self.start_time = None
            self.start_memory = None
            self.start_cpu = None
        
        def start(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss
            self.start_cpu = self.process.cpu_percent()
        
        def stop(self):
            end_time = time.time()
            end_memory = self.process.memory_info().rss
            end_cpu = self.process.cpu_percent()
            
            return {
                'duration': end_time - self.start_time,
                'memory_delta': (end_memory - self.start_memory) / 1024 / 1024,  # MB
                'cpu_delta': end_cpu - self.start_cpu
            }
    
    return PerformanceMonitor()


# Importações necessárias
from decimal import Decimal
from datetime import datetime, timezone, timedelta
