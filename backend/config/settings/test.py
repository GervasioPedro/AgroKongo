"""Settings para a suite de testes (pytest-django).

- SQLite em memória;
- Cache local (sem depender de Redis);
- Rate limiting desligado.
"""
from config.settings.base import *  # noqa: F401,F403

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

SESSION_INACTIVE_TIMEOUT_MINUTES = 120
