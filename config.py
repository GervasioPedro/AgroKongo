import os
from datetime import timedelta

# String de conexão para o PostgreSQL local (usando Docker)
POSTGRES_LOCAL_URI = 'postgresql://agrokongo_user:agrokongo_pass@localhost:5432/agrokongo_dev'

class Config:
    # --- CAMINHOS E DIRETÓRIOS ---
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    UPLOAD_BASE_PATH = os.environ.get('UPLOAD_PATH') or os.path.join(BASE_DIR, 'data_storage')
    UPLOAD_FOLDER_PUBLIC = os.path.join(UPLOAD_BASE_PATH, 'public')
    UPLOAD_FOLDER_PRIVATE = os.path.join(UPLOAD_BASE_PATH, 'private')

    # --- STORAGE EXTERNO (opcional) ---
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_SERVICE_ROLE = os.environ.get('SUPABASE_SERVICE_ROLE')  # manter secreto (Render)
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'agrokongo-uploads')
    SUPABASE_PUBLIC_URL = os.environ.get('SUPABASE_PUBLIC_URL')  # ex: https://<proj>.supabase.co/storage/v1

    # --- SEGURANÇA ---
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = 3600

    # --- LIMITES E NEGÓCIO ---
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    AGROKONGO_TAXA = 0.05
    ITEMS_PER_PAGE = 12
    TIMEZONE = 'Africa/Luanda'

class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-CHANGE-IN-PRODUCTION'
    # Respeitar variável de ambiente de teste antes de usar PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              os.environ.get('DEV_DATABASE_URL') or \
                              POSTGRES_LOCAL_URI
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_DOMAIN = None

class ProductionConfig(Config):
    DEBUG = False
    uri = os.environ.get('DATABASE_URL')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = uri
    
    # CORS: Apenas domínios explícitos via variável de ambiente
    # Em produção, usar APENAS o domínio do frontend (Netlify)
    _cors_allowed = os.environ.get('FRONTEND_URL', '').strip()
    if _cors_allowed:
        # Suporta múltiplos domínios separados por vírgula
        CORS_ORIGINS = [domain.strip() for domain in _cors_allowed.split(',') if domain.strip()]
    else:
        # Fallback seguro: apenas domínio principal
        CORS_ORIGINS = ['https://agrokongo.netlify.app']
    
    # Validar se todos os domínios usam HTTPS em produção
    for origin in CORS_ORIGINS:
        if not origin.startswith('https://') and 'localhost' not in origin:
            raise ValueError(f"ERRO DE SEGURANÇA: CORS_ORIGINS deve usar HTTPS. Encontrado: {origin}")
    
    REDIS_URL = os.environ.get('REDIS_URL')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    # Para Netlify (front) + Render (API) em domínios diferentes
    SESSION_COOKIE_SAMESITE = 'None'
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }

    @classmethod
    def init_app(cls, app):
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("ERRO DE SEGURANÇA: SECRET_KEY de produção não configurada!")
        if not os.environ.get('DATABASE_URL'):
            raise ValueError("ERRO CRÍTICO: DATABASE_URL não configurada em produção.")

config_dict = {
    'dev': DevelopmentConfig,
    'development': DevelopmentConfig,
    'prod': ProductionConfig,
    'production': ProductionConfig
}
