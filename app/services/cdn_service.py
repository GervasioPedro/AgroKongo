"""
Serviço de Upload para CDN.
Integração com AWS S3, Cloudflare R2, ou similar.
"""
import os
import boto3
from botocore.config import Config
from flask import current_app
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CDNService:
    """Gerencia upload e entrega de imagens via CDN."""
    
    def __init__(self):
        self.enabled = current_app.config.get('CDN_ENABLED', False)
        self.cdn_url = current_app.config.get('CDN_URL', '')
        self.bucket = current_app.config.get('CDN_BUCKET', 'agrokongo-safras')
        
        # Configurar cliente S3/Boto3 se CDN estiver habilitado
        if self.enabled:
            access_key = current_app.config.get('CDN_AWS_ACCESS_KEY')
            secret_key = current_app.config.get('CDN_AWS_SECRET_KEY')
            region = current_app.config.get('CDN_AWS_REGION', 'us-east-1')
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3}
                )
            )
            logger.info("CDN Service initialized with S3/Cloudflare R2")
        else:
            self.s3_client = None
            logger.info("CDN Service disabled - using local storage")
    
    def upload_imagem_safra(self, file_path: str, filename: str, 
                            content_type: str = 'image/webp') -> Tuple[bool, str]:
        """
        Faz upload de imagem para CDN.
        
        Args:
            file_path: Caminho local do ficheiro
            filename: Nome único do ficheiro (já sanitizado)
            content_type: MIME type do ficheiro
            
        Returns:
            Tuple[success, url_publica]
        """
        if not self.enabled or not self.s3_client:
            return False, ""
        
        try:
            key = f"safras/{filename}"
            
            with open(file_path, 'rb') as f:
                self.s3_client.upload_fileobj(
                    f,
                    self.bucket,
                    key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'ACL': 'public-read',
                        'CacheControl': 'public, max-age=31536000'  # 1 ano
                    }
                )
            
            # URL pública da imagem
            image_url = f"{self.cdn_url}/{key}" if self.cdn_url else \
                       f"https://{self.bucket}.s3.amazonaws.com/{key}"
            
            logger.info(f"Imagem enviada para CDN: {image_url}")
            return True, image_url
            
        except Exception as e:
            logger.error(f"Erro ao upload para CDN: {e}")
            return False, str(e)
    
    def delete_imagem(self, filename: str) -> bool:
        """Remove imagem da CDN."""
        if not self.enabled or not self.s3_client:
            return False
        
        try:
            key = f"safras/{filename}"
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Imagem removida da CDN: {filename}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar da CDN: {e}")
            return False
    
    def get_url_publica(self, filename: str) -> str:
        """Retorna URL pública da imagem."""
        if not self.enabled:
            # Fallback para armazenamento local
            return f"/uploads/safras/{filename}"
        
        if self.cdn_url:
            return f"{self.cdn_url}/safras/{filename}"
        else:
            return f"https://{self.bucket}.s3.amazonaws.com/safras/{filename}"
    
    def prefetch_urls(self, filenames: list) -> list:
        """
        Gera URLs em lote para múltiplas imagens (otimização).
        Útil para listas de safras.
        """
        return [self.get_url_publica(f) for f in filenames]


# Instância global (inicializada após app criado)
cdn_service = CDNService()


def init_cdn(app):
    """Inicializa serviço CDN com contexto da app."""
    global cdn_service
    with app.app_context():
        cdn_service = CDNService()
