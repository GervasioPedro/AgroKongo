"""
Configuração do Sentry para monitoramento de erros e performance.
"""
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import os


def init_sentry(app):
    """
    Inicializa Sentry com configurações otimizadas para produção.
    
    Args:
        app: Instância da aplicação Flask
    """
    sentry_dsn = os.environ.get('SENTRY_DSN')
    environment = os.environ.get('FLASK_ENV', 'development')
    
    if not sentry_dsn:
        app.logger.warning("Sentry DSN não configurado. Monitoramento desativado.")
        return
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(),
            RedisIntegration(),
            SqlalchemyIntegration(),
        ],
        environment=environment,
        
        # Taxa de amostragem para traces (performance monitoring)
        traces_sample_rate=0.1 if environment == 'production' else 0.5,
        
        # Capturar exceções automaticamente
        send_default_pii=True,  # Enviar dados pessoais (cuidado em produção)
        
        # Filtros personalizados
        before_send=before_send_handler,
        
        # Performance monitoring
        profiles_sample_rate=0.1,  # Coletar perfis de performance
        
        # Release tracking
        release=os.environ.get('SENTRY_RELEASE', 'agrokongo@1.0.0'),
    )
    
    app.logger.info(f"Sentry initialized for {environment} environment")


def before_send_handler(event, hint):
    """
    Handler personalizado para filtrar eventos antes de enviar ao Sentry.
    
    Args:
        event: Evento do Sentry
        hint: Informações adicionais sobre o erro
        
    Returns:
        event modificado ou None para descartar
    """
    # Não enviar erros de rotas 404 (muito ruído)
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        
        # Ignorar erros esperados (validações de negócio)
        from werkzeug.exceptions import HTTPException
        if isinstance(exc_value, HTTPException):
            if exc_value.code == 404:
                return None
        
        # Ignorar erros de CSRF (comuns e esperados)
        if 'CSRF' in str(exc_value):
            return None
    
    # Adicionar contexto adicional
    if 'extra' not in event:
        event['extra'] = {}
    
    event['extra']['application'] = 'agrokongo-core'
    
    return event


# Decorator para capturar erros específicos
def capture_exception(func):
    """
    Decorator para capturar exceções manualmente no Sentry.
    
    Uso:
        @capture_exception
        def processar_pagamento():
            ...
    """
    from functools import wraps
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise
    
    return wrapper


# Função utilitária para adicionar breadcrumbs
def add_breadcrumb(category: str, message: str, level: str = 'info', **kwargs):
    """
    Adiciona breadcrumb para debugging contextual.
    
    Uso:
        add_breadcrumb(
            category='pagamento',
            message='Iniciando processamento',
            level='info',
            transacao_id=123
        )
    """
    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=kwargs
    )
