from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate # IMPORTANTE: Adiciona esta linha

# Inicialização das Instâncias (Globais)
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate() # IMPORTANTE: Adiciona esta instância

def init_extensions(app):
    """
    Função responsável por iniciar as extensões junto da aplicação Flask.
    """
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db) # Inicializa o migrate aqui

    # Configurações do Login Manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Acesso restrito. Por favor, faça login primeiro."
    login_manager.login_message_category = "info"