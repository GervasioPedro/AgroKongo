import pytest
from app import create_app
from app.extensions import db as _db
from app.models import Usuario, Provincia, Municipio, Produto, Safra, Transacao


@pytest.fixture(scope='session')
def app():
    """
    Cria uma instância de aplicação para o contexto dos testes.
    Usa a configuração 'testing' definida no config.py (se existir)
    ou força as configurações aqui.
    """
    app = create_app('dev') # Usamos 'dev' mas sobrepomos configurações críticas
    
    # Configurações forçadas para teste
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", # Base de dados em RAM (rápida e isolada)
        "WTF_CSRF_ENABLED": False, # Desliga proteção CSRF para facilitar posts em teste
        "SERVER_NAME": "localhost.localdomain", # Necessário para url_for funcionar sem request context
        "UPLOAD_FOLDER_PUBLIC": "/tmp/uploads/public",
        "UPLOAD_FOLDER_PRIVATE": "/tmp/uploads/private",
    })

    with app.app_context():
        _db.create_all() # Cria as tabelas na memória
        yield app
        _db.drop_all() # Limpa tudo no fim


@pytest.fixture(scope='function')
def client(app):
    """Um cliente de teste que simula um navegador."""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """
    Fixture de base de dados que limpa os dados após cada teste individual,
    mantendo as tabelas criadas pela fixture 'app'.
    """
    with app.app_context():
        yield _db
        _db.session.remove()
        # Limpar todas as tabelas para próximo teste
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()
