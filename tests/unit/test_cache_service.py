"""
Testes Unitários do Serviço de Cache
Testa a funcionalidade de cache estratégico com Redis.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
import json

from app.services.cache_service import CacheService


class TestCacheService:
    """Testes para o serviço de cache."""
    
    @pytest.fixture
    def mock_redis(self):
        """Cria um mock do Redis para testes."""
        with patch('app.services.cache_service.redis') as mock_redis:
            redis_instance = MagicMock()
            mock_redis.from_url.return_value = redis_instance
            yield redis_instance
    
    @pytest.fixture
    def cache(self, mock_redis):
        """Cria instância do CacheService com Redis mockado."""
        return CacheService()
    
    def test_key_safra_disponivel(self, cache):
        """Testa geração de chaves padronizadas."""
        key = cache._key_safra(123)
        assert key == "safra:123"
    
    def test_key_safras_disponiveis_com_filtros(self, cache):
        """Testa chave para lista de safras com filtros."""
        # Sem filtros
        key = cache._key_safras_disponiveis()
        assert key == "safras:disponiveis"
        
        # Com província
        key = cache._key_safras_disponiveis(provincia_id=1)
        assert key == "safras:disponiveis:prov:1"
        
        # Com categoria
        key = cache._key_safras_disponiveis(categoria_id=2)
        assert key == "safras:disponiveis:cat:2"
        
        # Com ambos
        key = cache._key_safras_disponiveis(provincia_id=1, categoria_id=2)
        assert key == "safras:disponiveis:prov:1:cat:2"
    
    def test_serialize_decimal(self, cache):
        """Testa serialização de valores Decimal."""
        data = {
            'preco': Decimal('2500.00'),
            'quantidade': Decimal('10.5')
        }
        
        serialized = cache._serialize(data)
        deserialized = cache._deserialize(serialized)
        
        assert deserialized['preco'] == '2500.00'
        assert deserialized['quantidade'] == '10.5'
    
    def test_set_get_cache(self, cache, mock_redis):
        """Testa operações básicas de set/get."""
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = json.dumps({'id': 1, 'nome': 'Teste'})
        
        # Set
        result = cache.set("teste:key", {'id': 1, 'nome': 'Teste'}, timedelta(minutes=10))
        assert result is True
        mock_redis.setex.assert_called_once()
        
        # Get
        result = cache.get("teste:key")
        assert result == {'id': 1, 'nome': 'Teste'}
        mock_redis.get.assert_called_once_with("teste:key")
    
    def test_delete_cache(self, cache, mock_redis):
        """Testa remoção de chave do cache."""
        mock_redis.delete.return_value = 1
        
        result = cache.delete("teste:key")
        assert result is True
        mock_redis.delete.assert_called_once_with("teste:key")
    
    def test_exists_cache(self, cache, mock_redis):
        """Testa verificação de existência de chave."""
        # Chave existe
        mock_redis.exists.return_value = 1
        assert cache.exists("teste:key") is True
        
        # Chave não existe
        mock_redis.exists.return_value = 0
        assert cache.exists("teste:key") is False
    
    def test_invalidate_pattern(self, cache, mock_redis):
        """Testa invalidação em lote por padrão."""
        mock_redis.keys.return_value = ['safra:1', 'safra:2', 'safra:3']
        mock_redis.delete.return_value = 3
        
        count = cache.invalidate_pattern("safra:*")
        assert count == 3
        mock_redis.keys.assert_called_once_with("safra:*")
    
    def test_cache_safra(self, cache, mock_redis):
        """Testa cache especifico de safra."""
        safra_data = {
            'id': 123,
            'produto': 'Mandioca',
            'quantidade': 1000
        }
        
        cache.cache_safra(safra_data)
        
        # Verificar que setex foi chamado
        assert mock_redis.setex.called
        args = mock_redis.setex.call_args
        assert args is not None
        assert args[0][0] == "safra:123"
    
    def test_get_safra_hit(self, cache, mock_redis):
        """Testa obtenção de safra com cache hit."""
        safra_json = json.dumps({'id': 123, 'produto': 'Mandioca'})
        mock_redis.get.return_value = safra_json
        
        result = cache.get_safra(123)
        
        assert result['id'] == 123
        assert result['produto'] == 'Mandioca'
        mock_redis.get.assert_called_once_with("safra:123")
    
    def test_get_safra_miss(self, cache, mock_redis):
        """Testa obtenção de safra com cache miss."""
        mock_redis.get.return_value = None
        
        result = cache.get_safra(123)
        
        assert result is None
    
    def test_invalidate_safra(self, cache, mock_redis):
        """Testa invalidação de cache de safra específica."""
        mock_redis.delete.return_value = 1
        
        result = cache.invalidate_safra(123)
        
        assert result is True
        mock_redis.delete.assert_called_once_with("safra:123")
    
    def test_cache_safras_disponiveis(self, cache, mock_redis):
        """Testa cache de lista de safras disponiveis."""
        safras = [
            {'id': 1, 'produto': 'Milho'},
            {'id': 2, 'produto': 'Mandioca'}
        ]
        
        cache.cache_safras_disponiveis(safras, provincia_id=1)
        
        # Verificar que setex foi chamado
        assert mock_redis.setex.called
        args = mock_redis.setex.call_args
        assert args is not None
        assert args[0][0] == "safras:disponiveis:prov:1"
    
    def test_invalidate_safras_cache(self, cache, mock_redis):
        """Testa invalidação de todo cache de safras."""
        mock_redis.keys.return_value = [
            'safras:disponiveis',
            'safras:disponiveis:prov:1',
            'safras:disponiveis:cat:2'
        ]
        mock_redis.delete.return_value = 3
        
        count = cache.invalidate_safras_cache()
        assert count == 3
    
    def test_cached_decorator(self, cache, mock_redis):
        """Testa decorator de cache automático."""
        # Simular cache miss primeiro, depois hit
        mock_redis.get.side_effect = [None, json.dumps({'resultado': 42})]
        mock_redis.setex.return_value = True
        
        @cache.cached(
            key_generator=lambda args, kwargs: f"calculo:{kwargs.get('valor')}",
            ttl=timedelta(minutes=5)
        )
        def calculo_caro(valor):
            return {'resultado': valor * 2}
        
        # Primeira chamada (cache miss)
        result1 = calculo_caro(valor=21)
        assert result1 == {'resultado': 42}
        
        # Segunda chamada (cache hit)
        result2 = calculo_caro(valor=21)
        assert result2 == {'resultado': 42}
        
        # Redis deve ter sido chamado 2 vezes (get)
        assert mock_redis.get.call_count == 2


class TestCacheServiceErrorHandling:
    """Testa tratamento de erros do CacheService."""
    
    @pytest.fixture
    def mock_redis_error(self):
        """Cria mock que lança exceções."""
        with patch('app.services.cache_service.redis') as mock_redis:
            redis_instance = MagicMock()
            redis_instance.get.side_effect = Exception("Redis connection error")
            redis_instance.setex.side_effect = Exception("Redis connection error")
            mock_redis.from_url.return_value = redis_instance
            yield redis_instance
    
    def test_get_with_error_returns_none(self, mock_redis_error):
        """Testa que get retorna None em caso de erro."""
        cache = CacheService()
        result = cache.get("teste:key")
        assert result is None
    
    def test_set_with_error_returns_false(self, mock_redis_error):
        """Testa que set retorna False em caso de erro."""
        cache = CacheService()
        result = cache.set("teste:key", {'data': 'value'})
        assert result is False
