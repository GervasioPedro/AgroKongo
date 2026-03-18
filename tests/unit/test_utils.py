"""
Testes Unitários de Utilitários e Decorators
Testa helpers, decorators e mixins.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from app.utils.status_helper import (
    status_to_value,
    value_to_status,
    get_status_description
)
from app.utils.db_mixins import SoftDeleteMixin, TimestampMixin
from app.models import TransactionStatus


class TestStatusHelper:
    """Testa funções auxiliares de TransactionStatus."""
    
    def test_status_to_value_from_enum(self):
        """Testa conversão de Enum para valor string."""
        result = status_to_value(TransactionStatus.PENDENTE)
        assert result == 'pendente'
        
        result = status_to_value(TransactionStatus.FINALIZADO)
        assert result == 'finalizada'
    
    def test_status_to_value_from_string(self):
        """Testa conversão de string para valor string (pass-through)."""
        result = status_to_value('pendente')
        assert result == 'pendente'
        
        result = status_to_value('finalizada')
        assert result == 'finalizada'
    
    def test_status_to_value_invalid_string(self):
        """Testa erro com string inválida."""
        with pytest.raises(ValueError) as excinfo:
            status_to_value('status_invalido')
        
        assert "inválido" in str(excinfo.value).lower()
    
    def test_status_to_value_invalid_type(self):
        """Testa erro com tipo inválido."""
        with pytest.raises(TypeError) as excinfo:
            status_to_value(123)
        
        assert "tipo" in str(excinfo.value).lower()
    
    def test_value_to_status_from_string(self):
        """Testa conversão de string para Enum."""
        result = value_to_status('pendente')
        assert result == TransactionStatus.PENDENTE
        
        result = value_to_status('finalizada')
        assert result == TransactionStatus.FINALIZADO
    
    def test_value_to_status_from_enum(self):
        """Testa conversão de Enum para Enum (pass-through)."""
        result = value_to_status(TransactionStatus.PENDENTE)
        assert result == TransactionStatus.PENDENTE
    
    def test_value_to_status_invalid(self):
        """Testa erro com valor inválido."""
        with pytest.raises(ValueError) as excinfo:
            value_to_status('invalido')
        
        assert "inválido" in str(excinfo.value).lower()
    
    def test_get_status_description(self):
        """Testa obtenção de descrição amigável."""
        desc = get_status_description('pendente')
        assert desc is not None
        assert len(desc) > 0
        
        desc = get_status_description(TransactionStatus.FINALIZADO)
        assert desc is not None


class TestSoftDeleteMixin:
    """Testa funcionalidade de soft delete."""
    
    def test_soft_delete_marca_registro(self):
        """Testa que soft_delete marca deleted_at."""
        # Criar mock de modelo com mixin
        model = Mock(spec=SoftDeleteMixin)
        model.deleted_at = None
        
        # Aplicar metodo do mixin
        SoftDeleteMixin.soft_delete(model)
        
        assert model.deleted_at is not None
        assert isinstance(model.deleted_at, datetime)
    
    def test_restore_limpa_deleted_at(self):
        """Testa que restore limpa deleted_at."""
        model = Mock(spec=SoftDeleteMixin)
        model.deleted_at = datetime.now(timezone.utc)
        
        SoftDeleteMixin.restore(model)
        
        assert model.deleted_at is None
    
    def test_is_deleted_property(self):
        """Testa property is_deleted."""
        # Nao deletado
        model_nao_deletado = Mock(spec=SoftDeleteMixin)
        model_nao_deletado.deleted_at = None
        assert SoftDeleteMixin.is_deleted.fget(model_nao_deletado) is False
        
        # Deletado
        model_deletado = Mock(spec=SoftDeleteMixin)
        model_deletado.deleted_at = datetime.now(timezone.utc)
        assert SoftDeleteMixin.is_deleted.fget(model_deletado) is True


class TestTimestampMixin:
    """Testa mixin de timestamps automáticos."""
    
    def test_update_updated_at_callback(self):
        """Testa callback de atualização de timestamp."""
        model = Mock(spec=TimestampMixin)
        
        TimestampMixin._update_updated_at(None, None, model)
        
        model.updated_at = datetime.now(timezone.utc)


class TestHelpersGerais:
    """Testa funções helper gerais."""
    
    def test_formatar_moeda_kz(self):
        """Testa formatação de moeda angolana."""
        from app.utils.helpers import formatar_moeda_kz
        
        # Teste com valor inteiro
        assert formatar_moeda_kz(1000) == "1.000,00 Kz"
        
        # Teste com decimais
        assert formatar_moeda_kz(Decimal('2500.50')) == "2.500,50 Kz"
        
        # Teste com zero
        assert formatar_moeda_kz(0) == "0,00 Kz"
        
        # Teste com None
        assert formatar_moeda_kz(None) == "0,00 Kz"
    
    def test_formatar_nif(self):
        """Testa limpeza de NIF."""
        from app.utils.helpers import formatar_nif
        
        # Remove caracteres especiais
        assert formatar_nif("501234400001") == "501234400001"
        assert formatar_nif("501.234.400.001") == "501234400001"
        assert formatar_nif("501-234-400-001") == "501234400001"
        
        # Converte para maiúsculas
        assert formatar_nif("abc123") == "ABC123"
        
        # None retorna vazio
        assert formatar_nif(None) == ""
