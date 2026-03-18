"""
Serviço de Cache Estratégico para AgroKongo.
Cache em Redis para vitrine de produtos e dados frequentemente acessados.
"""
import redis
import json
from typing import Optional, List, Dict, Any
from datetime import timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Gerencia cache estratégico com Redis."""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.default_ttl = timedelta(minutes=15)
        
    # --- CHAVES PADRONIZADAS ---
    @staticmethod
    def _key_safra(safra_id: int) -> str:
        return f"safra:{safra_id}"
    
    @staticmethod
    def _key_safras_disponiveis(provincia_id: Optional[int] = None, 
                                  categoria_id: Optional[int] = None) -> str:
        key = "safras:disponiveis"
        if provincia_id:
            key += f":prov:{provincia_id}"
        if categoria_id:
            key += f":cat:{categoria_id}"
        return key
    
    @staticmethod
    def _key_produto(nome: str) -> str:
        return f"produto:{nome.lower().replace(' ', '_')}"
    
    @staticmethod
    def _key_produtor(produtor_id: int) -> str:
        return f"produtor:{produtor_id}"
    
    @staticmethod
    def _key_stats_dashboard() -> str:
        return "stats:dashboard:admin"
    
    # --- SERIALIZAÇÃO INTELIGENTE ---
    @staticmethod
    def _serialize(data: Any) -> str:
        """Serializa dados para JSON, lidando com Decimal e datetime."""
        def default_serializer(obj):
            if isinstance(obj, Decimal):
                return str(obj)
            elif hasattr(obj, 'isoformat'):  # datetime
                return obj.isoformat()
            return str(obj)
        
        return json.dumps(data, default=default_serializer)
    
    @staticmethod
    def _deserialize(data: str) -> Any:
        """Desserializa JSON para dict/list."""
        if not data:
            return None
        return json.loads(data)
    
    # --- OPERAÇÕES DE CACHE ---
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        try:
            data = self.redis.get(key)
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Erro ao obter cache {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Armazena valor no cache com TTL."""
        try:
            serialized = self._serialize(value)
            expire_seconds = int((ttl or self.default_ttl).total_seconds())
            return self.redis.setex(key, expire_seconds, serialized)
        except Exception as e:
            logger.error(f"Erro ao definir cache {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Remove valor do cache."""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Erro ao deletar cache {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Verifica se chave existe no cache."""
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Erro ao verificar cache {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalida todas as chaves que match com um padrão."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Erro ao invalidar padrão {pattern}: {e}")
            return 0
    
    # --- MÉTODOS ESPECÍFICOS PARA SAFRAS ---
    def cache_safra(self, safra_data: Dict) -> bool:
        """Cache de dados de uma safra específica."""
        key = self._key_safra(safra_data['id'])
        return self.set(key, safra_data, ttl=timedelta(minutes=30))
    
    def get_safra(self, safra_id: int) -> Optional[Dict]:
        """Obtém safra do cache."""
        return self.get(self._key_safra(safra_id))
    
    def invalidate_safra(self, safra_id: int) -> bool:
        """Invalida cache de uma safra."""
        return self.delete(self._key_safra(safra_id))
    
    def cache_safras_disponiveis(self, safras: List[Dict], 
                                   provincia_id: Optional[int] = None,
                                   categoria_id: Optional[int] = None) -> bool:
        """Cache da lista de safras disponíveis."""
        key = self._key_safras_disponiveis(provincia_id, categoria_id)
        return self.set(key, safras, ttl=timedelta(minutes=10))
    
    def get_safras_disponiveis(self, provincia_id: Optional[int] = None,
                                categoria_id: Optional[int] = None) -> Optional[List[Dict]]:
        """Obtém lista de safras do cache."""
        return self.get(self._key_safras_disponiveis(provincia_id, categoria_id))
    
    def invalidate_safras_cache(self) -> int:
        """Invalida todo cache de safras (útil quando há nova safra)."""
        return self.invalidate_pattern("safras:*")
    
    # --- CACHE DE ESTATÍSTICAS DO DASHBOARD ---
    def cache_dashboard_stats(self, stats: Dict) -> bool:
        """Cache de estatísticas do dashboard admin."""
        return self.set(self._key_stats_dashboard(), stats, ttl=timedelta(minutes=5))
    
    def get_dashboard_stats(self) -> Optional[Dict]:
        """Obtém estatísticas do cache."""
        return self.get(self._key_stats_dashboard())
    
    # --- DECORATOR PARA CACHE AUTOMÁTICO ---
    def cached(self, key_generator, ttl: Optional[timedelta] = None):
        """
        Decorator para cache automático de funções.
        
        Uso:
            @cache.cached(
                key_generator=lambda args, kwargs: f"produto:{kwargs.get('id')}",
                ttl=timedelta(minutes=15)
            )
            def obter_produto(id):
                ...
        """
        def decorator(func):
            from functools import wraps
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                key = key_generator(args, kwargs)
                
                # Tenta obter do cache
                cached_data = self.get(key)
                if cached_data is not None:
                    logger.debug(f"Cache HIT: {key}")
                    return cached_data
                
                # Executa função e cacheia resultado
                logger.debug(f"Cache MISS: {key}")
                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result
            
            return wrapper
        return decorator


# Instância global para uso na aplicação
cache_service = CacheService()
