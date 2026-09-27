"""Settings base do backend Django do AgroKongo.

Substitui o `config.py` do Flask. Diferenças de segurança importantes:
- SECRET_KEY SEM OBRIGATÓRIO em produção (sem fallback hardcoded);
- DATABASE_URL via dj-database-url (Postgres), SQLite apenas para dev/testes;
- Rate limiting e cache no Redis configuráveis por variável de ambiente.
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # raiz do repo

# --- Segurança -------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("FLASK_ENV", os.environ.get("DJANGO_ENV", "dev")) in ("dev", "development", "True", "true")
ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else ""
).split(",")

if not SECRET_KEY and not DEBUG:
    raise RuntimeError(
        "SECRET_KEY não definida. Em produção é obrigatória — sem valor padrão."
    )
if not SECRET_KEY:  # só em dev
    SECRET_KEY = "dev-insecure-not-for-production"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "rest_framework",
    "corsheaders",
    "django_filters",
    # Apps do domínio
    "apps.core",
    "apps.geo",
    "apps.accounts",
    "apps.catalogo",
    "apps.compras",
    "apps.chat",
    "apps.notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Base de dados ----------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "data_storage" / "agrokongo_django.sqlite3",
        }
    }
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.Usuario"

# --- Autenticação / API ------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.auth.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.core.exceptions.handler_api",
}

SESSION_INACTIVE_TIMEOUT_MINUTES = int(os.environ.get("SESSION_TIMEOUT_MIN", "120"))
RESET_TOKEN_MINUTES = int(os.environ.get("RESET_TOKEN_MIN", "30"))

# CORS — frontend React
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# --- Cache / Rate limit (Redis configurável, sem hardcoded) ------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache"
        if os.environ.get("REDIS_URL")
        else "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": REDIS_URL,
    }
}

# --- I18N --------------------------------------------------------------------
LANGUAGE_CODE = "pt"
TIME_ZONE = "Africa/Luanda"
USE_I18N = True
USE_TZ = True

# --- Estáticos / Média --------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/uploads/"
MEDIA_ROOT = BASE_DIR / "data_storage"

MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_MB", "5"))

# --- Logs ---------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simples": {"format": "[{asctime}] {levelname} {name}: {message}",
                    "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simples"},
    },
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
