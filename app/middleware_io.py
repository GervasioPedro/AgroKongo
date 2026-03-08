"""
app/middleware.py
Middlewares para tratamento de timeout, retry e logs em operações I/O
"""
import time
import logging
from functools import wraps
from flask import request, g, current_app
from typing import Callable, Optional
import threading

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Exceção para operações que excederam o timeout"""
    pass


def request_timer(f: Callable) -> Callable:
    """
    Decorator para medir tempo de execução das requisições
    Adiciona headers de performance e logs detalhados
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        
        # Executa a requisição
        response = f(*args, **kwargs)
        
        # Calcula duração
        duration = time.time() - start_time
        
        # Adiciona header de timing (útil para debugging)
        if hasattr(response, 'headers'):
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        # Log para requisições lentas (> 2 segundos)
        if duration > 2.0:
            logger.warning(
                f"Requisição lenta: {request.method} {request.path} "
                f"({duration:.3f}s) - IP: {request.remote_addr}"
            )
        else:
            logger.debug(
                f"Requisição: {request.method} {request.path} "
                f"({duration:.3f}s)"
            )
        
        return response
    return decorated_function


def io_operation_timeout(timeout_seconds: float = 30.0, retries: int = 3):
    """
    Decorator para operações de I/O com timeout e retry
    
    Args:
        timeout_seconds: Timeout máximo em segundos
        retries: Número de tentativas de retry
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(retries):
                try:
                    # Cria thread para controlar timeout
                    result = [None]
                    exception = [None]
                    
                    def target():
                        try:
                            result[0] = func(*args, **kwargs)
                        except Exception as e:
                            exception[0] = e
                    
                    thread = threading.Thread(target=target)
                    thread.daemon = True
                    thread.start()
                    thread.join(timeout=timeout_seconds)
                    
                    if thread.is_alive():
                        # Thread ainda executando = timeout
                        error_msg = f"{func.__name__} excedeu timeout de {timeout_seconds}s"
                        logger.error(error_msg)
                        raise TimeoutError(error_msg)
                    
                    if exception[0]:
                        raise exception[0]
                    
                    return result[0]
                    
                except TimeoutError:
                    last_exception = TimeoutError(f"Timeout na tentativa {attempt + 1}/{retries}")
                    if attempt < retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{retries} após timeout em {func.__name__}")
                        time.sleep(1.0 * (attempt + 1))  # Backoff linear
                    else:
                        logger.error(f"{func.__name__} falhou após {retries} tentativas")
                        raise
                        
                except Exception as e:
                    last_exception = e
                    logger.exception(f"Erro em {func.__name__} (tentativa {attempt + 1}/{retries}): {str(e)}")
                    if attempt >= retries - 1:
                        break
                    time.sleep(0.5 * (attempt + 1))
            
            raise type(last_exception)(
                f"{func.__name__} falhou após {retries} tentativas: {str(last_exception)}"
            )
        
        return wrapper
    return decorator


class RequestLoggingMiddleware:
    """
    Middleware para log detalhado de todas as requisições
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
    
    def before_request(self):
        """Executado antes de cada requisição"""
        g.start_time = time.time()
        
        # Log informações da requisição
        logger.info(
            f"REQUEST INICIADA: {request.method} {request.path} | "
            f"IP: {request.remote_addr} | "
            f"User-Agent: {request.user_agent.string[:100] if request.user_agent else 'Unknown'}"
        )
        
        # Em debug, logar headers e body
        if current_app.debug and request.data:
            logger.debug(f"Request Body: {request.data[:500]}")
    
    def after_request(self, response):
        """Executado após cada requisição bem-sucedida"""
        duration = time.time() - g.start_time
        
        # Log resultado
        logger.info(
            f"REQUEST COMPLETA: {request.method} {request.path} | "
            f"Status: {response.status_code} | "
            f"Duração: {duration:.3f}s"
        )
        
        # Adiciona header de timing
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
    
    def teardown_request(self, exception):
        """Executado após cada requisição, mesmo com erro"""
        if exception:
            logger.error(
                f"REQUEST COM ERRO: {request.method} {request.path} | "
                f"Erro: {str(exception)}",
                exc_info=True
            )


class SlowQueryLogger:
    """
    Logger para queries lentas do SQLAlchemy
    """
    
    def __init__(self, threshold_seconds: float = 1.0):
        self.threshold = threshold_seconds
    
    def __call__(self, cursor, statement, parameters, context):
        """Hook executado após cada query SQL"""
        # Nota: Este hook requer configuração adicional no SQLAlchemy
        # Para implementação completa, usar event.listens_for no modelo
        pass


def rate_limit_by_ip(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator para rate limiting baseado em IP com janela deslizante
    
    Args:
        max_requests: Número máximo de requisições por janela
        window_seconds: Tamanho da janela em segundos
    """
    # Implementação simplificada - em produção usar Redis
    ip_requests = {}
    lock = threading.Lock()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr
            now = time.time()
            
            with lock:
                # Limpa IPs antigos
                expired = [ip for ip, times in ip_requests.items() 
                          if now - min(times) > window_seconds]
                for old_ip in expired:
                    del ip_requests[old_ip]
                
                # Verifica limite
                if ip in ip_requests:
                    recent_requests = [t for t in ip_requests[ip] 
                                      if now - t < window_seconds]
                    
                    if len(recent_requests) >= max_requests:
                        logger.warning(f"Rate limit excedido para IP {ip}")
                        from flask import jsonify
                        return jsonify({
                            'error': 'Rate limit excedido',
                            'retry_after': window_seconds
                        }), 429
                    
                    ip_requests[ip] = recent_requests
                else:
                    ip_requests[ip] = []
                
                ip_requests[ip].append(now)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Context manager para operações críticas
class OperationTimer:
    """
    Context manager para medir tempo de operações específicas
    
    Uso:
        with OperationTimer('upload_arquivo', logger):
            upload_file(...)
    """
    
    def __init__(self, operation_name: str, logger: logging.Logger = None, 
                 warning_threshold: float = 5.0):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.warning_threshold = warning_threshold
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Iniciando operação: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"Operação {self.operation_name} falhou após {duration:.3f}s: {exc_val}"
            )
        elif duration > self.warning_threshold:
            self.logger.warning(
                f"Operação lenta: {self.operation_name} ({duration:.3f}s)"
            )
        else:
            self.logger.info(
                f"Operação concluída: {self.operation_name} ({duration:.3f}s)"
            )
        
        return False  # Não suprime exceptions
