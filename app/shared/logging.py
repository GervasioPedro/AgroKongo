# app/shared/logging.py
"""
Logging Estruturado - AgroKongo

Este módulo configura o logging estruturado usando structlog para
garantir logs consistentes e facilitar integração com sistemas de
monitorização como ELK Stack ou Datadog.

Características:
- Formato JSON para logs
- Contexto de requisição
- Correlação de transações
- Sanitização de dados sensíveis
"""
import json
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime


class AgroKongoLogger:
    """
    Logger estruturado para o AgroKongo.
    
    Fornece métodos consistentes de logging com contexto adicional
    para operações de negócio.
    """
    
    def __init__(self, name: str = "agrokongo"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura o logger com handlers apropriados."""
        if not self.logger.handlers:
            # Handler para console (JSON em produção)
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # Handler para ficheiro
            try:
                file_handler = logging.FileHandler('logs/agrokongo_structured.log')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except (OSError, FileNotFoundError):
                # Logs directory might not exist
                pass
            
            self.logger.setLevel(logging.INFO)
    
    def _format_log(self, event: str, context: Dict[str, Any] = None) -> str:
        """Formata o log como JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event': event,
            'service': 'agrokongo'
        }
        
        if context:
            # Sanitiza dados sensíveis
            sanitized_context = self._sanitize_sensitive_data(context)
            log_entry['context'] = sanitized_context
        
        return json.dumps(log_entry)
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove ou mascara dados sensíveis dos logs."""
        sensitive_fields = [
            'senha', 'password', 'senha_atual', 'nova_senha',
            'nif', 'iban', 'documento_pdf', 'comprovativo_path',
            'secret_key', 'api_key', 'token'
        ]
        
        sanitized = {}
        for key, value in data.items():
            if key.lower() in sensitive_fields:
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_sensitive_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def info(self, event: str, **context):
        """Log de informação."""
        self.logger.info(self._format_log(event, context if context else None))
    
    def warning(self, event: str, **context):
        """Log de aviso."""
        self.logger.warning(self._format_log(event, context if context else None))
    
    def error(self, event: str, error: Exception = None, **context):
        """Log de erro."""
        log_data = {
            'event': event,
        }
        
        if error:
            log_data['error_type'] = type(error).__name__
            log_data['error_message'] = str(error)
        
        if context:
            log_data['context'] = self._sanitize_sensitive_data(context)
        
        self.logger.error(json.dumps(log_data))
    
    def debug(self, event: str, **context):
        """Log de debug."""
        self.logger.debug(self._format_log(event, context if context else None))
    
    def audit(self, action: str, user_id: int = None, details: Dict = None, ip: str = None):
        """
        Log de auditoria para operações sensíveis.
        
        Args:
            action: Ação realizada (ex: "USER_LOGIN", "TRANSACTION_CREATED")
            user_id: ID do utilizador
            details: Detalhes adicionais
            ip: IP do utilizador
        """
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': 'AUDIT',
            'action': action,
            'user_id': user_id,
            'ip': ip,
            'details': self._sanitize_sensitive_data(details or {})
        }
        
        self.logger.info(json.dumps(audit_entry))


# Logger global
logger = AgroKongoLogger()


# ============================================================
# Context Managers para logging
# ============================================================

class LogContext:
    """
    Context Manager para adicionar contexto aos logs.
    
    Uso:
        with LogContext(operation="create_transaction", user_id=123) as ctx:
            # Código da operação
            ctx.success()  # Regista sucesso
    """
    
    def __init__(self, operation: str, user_id: int = None, **context):
        self.operation = operation
        self.user_id = user_id
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        logger.info(
            f"{self.operation}_started",
            operation=self.operation,
            user_id=self.user_id,
            **self.context
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type is None:
            logger.info(
                f"{self.operation}_completed",
                operation=self.operation,
                user_id=self.user_id,
                duration_seconds=duration,
                **self.context
            )
        else:
            logger.error(
                f"{self.operation}_failed",
                error=exc_val,
                operation=self.operation,
                user_id=self.user_id,
                duration_seconds=duration,
                **self.context
            )
        return False  # Propaga a exceção
    
    def success(self, **additional_context):
        """Regista sucesso da operação."""
        self.context.update(additional_context)


# ============================================================
# Decorators para logging
# ============================================================

def log_operation(operation_name: str):
    """
    Decorator para log automático de operações.
    
    Uso:
        @log_operation("create_user")
        def create_user(data):
            # código
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LogContext(operation=operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def audit_log(action: str):
    """
    Decorator para log de auditoria.
    
    Uso:
        @audit_log("TRANSACTION_CREATED")
        def create_transaction(user_id, data):
            # código
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or (args[0] if args else None)
            result = func(*args, **kwargs)
            
            logger.audit(
                action=action,
                user_id=user_id,
                details={'args': str(args), 'kwargs': list(kwargs.keys())}
            )
            
            return result
        return wrapper
    return decorator


# ============================================================
# Exports
# ============================================================

__all__ = [
    'logger',
    'AgroKongoLogger',
    'LogContext',
    'log_operation',
    'audit_log',
]
