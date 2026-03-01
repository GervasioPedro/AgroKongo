import os
from datetime import timedelta


class Config:
    # --- CAMINHOS E DIRETÓRIOS ---
    # Caminho absoluto para a raiz do projeto
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Armazenamento: Fora da pasta 'app' para persistência em servidores VPS
    UPLOAD_BASE_PATH = os.environ.get('UPLOAD_PATH') or os.path.join(BASE_DIR, 'data_storage')
    UPLOAD_FOLDER_PUBLIC = os.path.join(UPLOAD_BASE_PATH, 'public')
    UPLOAD_FOLDER_PRIVATE = os.path.join(UPLOAD_BASE_PATH, 'private')

    # --- SEGURANÇA ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'agro-kongo-local-dev-key-2024'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora para expiração de formulários

    # --- LIMITES E TIMEOUTS ---
    # 16MB é generoso, mas cuidado com a RAM do servidor.
    # O nosso helper 'salvar_ficheiro' já redimensiona, então isto é apenas um teto.
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # Aumentado para melhor UX em Angola

    # --- NEGÓCIO (Single Source of Truth) ---
    AGROKONGO_TAXA = 0.05
    ITEMS_PER_PAGE = 12
    TIMEZONE = 'Africa/Luanda'


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              f"sqlite:///{os.path.join(Config.BASE_DIR, 'agrokongo_dev.db')}"

    # Em dev, permitimos cookies sem HTTPS
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False

    # Base de Dados Profissional (PostgreSQL recomendado)
    uri = os.environ.get('DATABASE_URL')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = uri

    # --- SEGURANÇA DE COOKIES (ESSENCIAL PARA HTTPS/PRODUÇÃO) ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # --- PERFORMANCE: POOL DE CONEXÕES ---
    # Evita o erro 'Too many clients' no PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,  # Conexões fixas
        "max_overflow": 20,  # Conexões extras em pico de tráfego
        "pool_recycle": 1800,  # Reinicia conexões a cada 30min
        "pool_pre_ping": True,  # Verifica se a DB está viva antes de cada query
    }

    @classmethod
    def init_app(cls, app):
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'agro-kongo-local-dev-key-2024':
            raise ValueError("ERRO DE SEGURANÇA: SECRET_KEY de produção não configurada!")





config_dict = {
    'dev': DevelopmentConfig,
    'development': DevelopmentConfig,  # <-- ADICIONA ESTA LINHA
    'prod': ProductionConfig,
    'production': ProductionConfig
}