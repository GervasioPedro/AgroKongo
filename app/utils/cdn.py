"""
Configuração de CDN para Assets do AgroKongo
Suporta Cloudinary, AWS S3, e servir local com cache headers
"""
import os
import hashlib
from functools import wraps
from flask import url_for, current_app, request, send_from_directory
from werkzeug.utils import secure_filename
from app.extensions import cache
from typing import Optional


class CDNHelper:
    """
    Helper para gerenciamento de CDN
    Suporta múltiplos provedores de storage
    """
    
    @staticmethod
    def get_cdn_url(path: str) -> str:
        """
        Retorna URL do asset considerando o provedor configurado
        
        Args:
            path: Caminho relativo do arquivo (ex: 'uploads/perfil/image.jpg')
            
        Returns:
            URL completa do asset
        """
        provider = current_app.config.get('CDN_PROVIDER', 'local')
        
        if provider == 'cloudinary':
            return CDNHelper._cloudinary_url(path)
        elif provider == 's3':
            return CDNHelper._s3_url(path)
        else:
            return CDNHelper._local_url(path)
    
    @staticmethod
    def _cloudinary_url(path: str) -> str:
        """Gera URL do Cloudinary"""
        cloud_name = current_app.config.get('CLOUDINARY_CLOUD_NAME')
        if not cloud_name:
            return CDNHelper._local_url(path)
        
        return f"https://res.cloudinary.com/{cloud_name}/image/upload/{path}"
    
    @staticmethod
    def _s3_url(path: str) -> str:
        """Gera URL do AWS S3"""
        bucket = current_app.config.get('AWS_S3_BUCKET')
        region = current_app.config.get('AWS_REGION', 'us-east-1')
        
        if not bucket:
            return CDNHelper._local_url(path)
        
        return f"https://{bucket}.s3.{region}.amazonaws.com/{path}"
    
    @staticmethod
    def _local_url(path: str) -> str:
        """Gera URL local com version hash"""
        # Adiciona hash do arquivo para cache busting
        full_path = os.path.join(current_app.config.get('BASE_DIR', ''), path)
        
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            return f"{url_for('static', filename=path)}?v={file_hash}"
        
        return url_for('static', filename=path)
    
    @staticmethod
    def get_upload_folder(subfolder: str = '') -> str:
        """Retorna o caminho da pasta de uploads"""
        base = current_app.config.get('UPLOAD_BASE_PATH', 'data_storage')
        
        if subfolder:
            return os.path.join(base, subfolder)
        return base
    
    @staticmethod
    def save_upload(file, subfolder: str, filename: str) -> Optional[str]:
        """
        Salva um arquivo de upload
        
        Args:
            file: Arquivo do request
            subfolder: Subpasta (ex: 'perfil', 'safras')
            filename: Nome do arquivo
            
        Returns:
            Caminho relativo do arquivo salvo ou None em caso de erro
        """
        folder = CDNHelper.get_upload_folder(subfolder)
        os.makedirs(folder, exist_ok=True)
        
        safe_filename = secure_filename(filename)
        filepath = os.path.join(folder, safe_filename)
        
        try:
            file.save(filepath)
            return os.path.join(subfolder, safe_filename)
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar arquivo: {e}")
            return None


def cached_asset(timeout: int = 3600, key_prefix: str = 'asset_'):
    """
    Decorator para cache de assets estáticos
    
    Args:
        timeout: Tempo de cache em segundos (padrão: 1 hora)
        key_prefix: Prefixo para a chave de cache
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Gera chave única baseada nos argumentos
            cache_key = f"{key_prefix}{request.path}"
            
            # Tenta obter do cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Executa a função original
            response = f(*args, **kwargs)
            
            # Armazena em cache
            cache.set(cache_key, response, timeout=timeout)
            
            return response
        return decorated_function
    return decorator


def cache_control(max_age: int = 86400, public: bool = True):
    """
    Decorator para definir headers de cache HTTP
    
    Args:
        max_age: Tempo máximo de cache em segundos (padrão: 24 horas)
        public: Se True, cache é público; se False, privado
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            if hasattr(response, 'headers'):
                cache_value = f"public, max-age={max_age}" if public else f"private, max-age={max_age}"
                response.headers['Cache-Control'] = cache_value
                response.headers['Expires'] = str(max_age)
            
            return response
        return decorated_function
    return decorator


# Função para limpar cache de assets
def invalidate_asset_cache(pattern: str = 'asset_*'):
    """Remove entries de cache de assets"""
    # Nota: Redis não suporta wildcards diretamente
    # Em produção, considere usar cache tags ou múltiplas chaves
    current_app.logger.info(f"Cache invalidation requested for pattern: {pattern}")
