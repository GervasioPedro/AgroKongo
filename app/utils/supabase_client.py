"""
app/utils/supabase_client.py
Cliente Supabase com tratamento robusto de erros e logs
"""
import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class SupabaseClientError(Exception):
    """Exceção personalizada para erros do Supabase"""
    def __init__(self, message: str, status_code: int = None, original_error: Exception = None):
        self.message = message
        self.status_code = status_code
        self.original_error = original_error
        super().__init__(self.message)


def supabase_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator para retry em operações do Supabase
    
    Args:
        max_retries: Número máximo de tentativas
        delay: Delay inicial entre retries (segundos)
        backoff: Fator multiplicador do delay
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"Supabase {func.__name__} - Tentativa {attempt + 1}/{max_retries + 1}")
                    return func(*args, **kwargs)
                except SupabaseClientError as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Supabase {func.__name__} falhou (tentativa {attempt + 1}): {e.message}. "
                            f"Retry em {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"Supabase {func.__name__} falhou após {max_retries + 1} tentativas: {e.message}"
                        )
                except Exception as e:
                    last_exception = e
                    logger.exception(f"Erro inesperado em {func.__name__}: {str(e)}")
                    if attempt >= max_retries:
                        break
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            raise SupabaseClientError(
                f"{func.__name__} falhou após {max_retries + 1} tentativas",
                original_error=last_exception
            )
        return wrapper
    return decorator


class SupabaseStorageClient:
    """
    Cliente para operações no Supabase Storage com tratamento de erros
    """
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa cliente Supabase com validação"""
        try:
            from supabase import create_client, Client
            
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE')
            
            if not supabase_url or not supabase_key:
                logger.warning("SUPABASE_URL ou SUPABASE_SERVICE_ROLE não configurados")
                return
            
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info("Cliente Supabase inicializado com sucesso")
            
        except ImportError:
            logger.error("pacote 'supabase' não instalado. Execute: pip install supabase")
            self.client = None
        except Exception as e:
            logger.error(f"Falha ao inicializar cliente Supabase: {str(e)}")
            self.client = None
    
    @supabase_retry(max_retries=3, delay=1.0)
    def upload_file(self, bucket: str, file_path: str, file_data: bytes, 
                   content_type: str = 'application/octet-stream') -> Optional[str]:
        """
        Upload de arquivo para Supabase Storage
        
        Args:
            bucket: Nome do bucket
            file_path: Caminho relativo no bucket
            file_data: Dados binários do arquivo
            content_type: Tipo MIME do arquivo
            
        Returns:
            URL pública do arquivo ou None em caso de erro
        """
        if not self.client:
            logger.error("Cliente Supabase não inicializado")
            return None
        
        try:
            start_time = time.time()
            
            response = self.client.storage.from_(bucket).upload(
                file_path, 
                file_data,
                {'content-type': content_type}
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Upload concluído em {elapsed:.2f}s: {file_path}")
            
            # Retorna URL pública
            public_url = self.client.storage.from_(bucket).get_public_url(file_path)
            return public_url
            
        except Exception as e:
            error_msg = f"Falha no upload para {bucket}/{file_path}: {str(e)}"
            logger.error(error_msg)
            raise SupabaseClientError(error_msg, original_error=e)
    
    @supabase_retry(max_retries=3, delay=1.0)
    def download_file(self, bucket: str, file_path: str) -> Optional[bytes]:
        """
        Download de arquivo do Supabase Storage
        
        Args:
            bucket: Nome do bucket
            file_path: Caminho relativo no bucket
            
        Returns:
            Dados binários do arquivo ou None
        """
        if not self.client:
            logger.error("Cliente Supabase não inicializado")
            return None
        
        try:
            start_time = time.time()
            
            response = self.client.storage.from_(bucket).download(file_path)
            
            elapsed = time.time() - start_time
            logger.info(f"Download concluído em {elapsed:.2f}s: {file_path}")
            
            return response
            
        except Exception as e:
            error_msg = f"Falha no download de {bucket}/{file_path}: {str(e)}"
            logger.error(error_msg)
            raise SupabaseClientError(error_msg, original_error=e)
    
    @supabase_retry(max_retries=3, delay=1.0)
    def delete_file(self, bucket: str, file_paths: list) -> bool:
        """
        Deletar arquivos do Supabase Storage
        
        Args:
            bucket: Nome do bucket
            file_paths: Lista de caminhos relativos
            
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.client:
            logger.error("Cliente Supabase não inicializado")
            return False
        
        try:
            response = self.client.storage.from_(bucket).remove(file_paths)
            
            logger.info(f"Arquivos deletados: {file_paths}")
            return True
            
        except Exception as e:
            error_msg = f"Falha ao deletar arquivos: {str(e)}"
            logger.error(error_msg)
            raise SupabaseClientError(error_msg, original_error=e)
    
    @supabase_retry(max_retries=3, delay=1.0)
    def list_files(self, bucket: str, path: str = '', limit: int = 100) -> list:
        """
        Listar arquivos em uma pasta do bucket
        
        Args:
            bucket: Nome do bucket
            path: Caminho da pasta
            limit: Número máximo de arquivos
            
        Returns:
            Lista de metadados dos arquivos
        """
        if not self.client:
            logger.error("Cliente Supabase não inicializado")
            return []
        
        try:
            response = self.client.storage.from_(bucket).list(
                path=path,
                options={'limit': limit, 'offset': 0}
            )
            
            logger.info(f"{len(response)} arquivos listados em {bucket}/{path}")
            return response
            
        except Exception as e:
            error_msg = f"Falha ao listar arquivos: {str(e)}"
            logger.error(error_msg)
            raise SupabaseClientError(error_msg, original_error=e)


# Singleton global
_supabase_client: Optional[SupabaseStorageClient] = None


def get_supabase_client() -> Optional[SupabaseStorageClient]:
    """
    Obtém instância singleton do cliente Supabase
    
    Returns:
        Instância do cliente ou None se não configurado
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = SupabaseStorageClient()
    
    return _supabase_client


def supabase_enabled() -> bool:
    """
    Verifica se Supabase está configurado e disponível
    
    Returns:
        True se Supabase estiver configurado, False caso contrário
    """
    client = get_supabase_client()
    return client is not None and client.client is not None
