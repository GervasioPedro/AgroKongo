# app/domain/repositories/__init__.py
"""
Repository Interfaces - Padrão Repository do DDD

Este módulo define interfaces abstratas para acesso a dados,
promovendo baixo acoplamento e testabilidade.

Implementa o padrão Repository que:
- Abstrae a camada de persistência
- Permite substituição de implementações
- Facilita testes com mocks
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
from decimal import Decimal
from datetime import datetime


class RepositoryBase(ABC):
    """Classe base abstrata para todos os repositórios."""
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        """Obtém uma entidade pelo ID."""
        pass
    
    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Lista todas as entidades com paginação."""
        pass
    
    @abstractmethod
    def save(self, entity: Any) -> Any:
        """Salva ou atualiza uma entidade."""
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """Remove uma entidade pelo ID."""
        pass


class UsuarioRepository(RepositoryBase):
    """
    Interface para acesso a dados de Usuários.
    
    Métodos abstratos:
    - get_by_id: Busca por ID
    - get_by_telemovel: Busca por número de telemóvel
    - get_by_email: Busca por email
    - get_produtores: Lista produtores validados
    - get_compradores: Lista compradores
    - get_usuarios_por_provincia: Filtro por localização
    """
    
    @abstractmethod
    def get_by_telemovel(self, telemovel: str) -> Optional[Any]:
        """Busca usuário pelo telemóvel."""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[Any]:
        """Busca usuário pelo email."""
        pass
    
    @abstractmethod
    def get_produtores_validados(self, provincia_id: Optional[int] = None) -> List[Any]:
        """Lista produtores com conta validada."""
        pass
    
    @abstractmethod
    def get_compradores(self, limit: int = 50) -> List[Any]:
        """Lista compradores."""
        pass
    
    @abstractmethod
    def buscar_por_nome(self, termo: str, limite: int = 20) -> List[Any]:
        """Busca usuários por nome."""
        pass


class TransacaoRepository(RepositoryBase):
    """
    Interface para acesso a dados de Transações (Escrow).
    
    Métodos abstratos:
    - get_by_fatura_ref: Busca por referência de fatura
    - get_transacoes_comprador: Transações de um comprador
    - get_transacoes_vendedor: Transações de um vendedor
    - get_transacoes_status: Filtro por status
    - get_transacoes_pendentes: Transações em análise
    """
    
    @abstractmethod
    def get_by_fatura_ref(self, ref: str) -> Optional[Any]:
        """Busca transação pela referência da fatura."""
        pass
    
    @abstractmethod
    def get_transacoes_comprador(
        self, 
        comprador_id: int, 
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Any]:
        """Lista transações de um comprador."""
        pass
    
    @abstractmethod
    def get_transacoes_vendedor(
        self, 
        vendedor_id: int, 
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Any]:
        """Lista transações de um vendedor."""
        pass
    
    @abstractmethod
    def get_transacoes_por_status(self, status: str, limit: int = 50) -> List[Any]:
        """Lista transações por status."""
        pass
    
    @abstractmethod
    def get_transacoes_em_analise(self, horas: int = 24) -> List[Any]:
        """Transações em análise há mais de N horas."""
        pass
    
    @abstractmethod
    def calcular_receita_total(
        self, 
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> Decimal:
        """Calcula receita total da plataforma."""
        pass


class SafraRepository(RepositoryBase):
    """
    Interface para acesso a dados de Safras.
    
    Métodos abstratos:
    - get_safras_disponiveis: Safras com status disponível
    - get_safras_produtor: Safras de um produtor específico
    - buscar_por_produto: Filtro por tipo de produto
    - buscar_por_preco: Filtro por faixa de preço
    - get_safras_recentes: Últimas safras publicadas
    """
    
    @abstractmethod
    def get_safras_disponiveis(
        self, 
        produto_id: Optional[int] = None,
        provincia_id: Optional[int] = None,
        preco_min: Optional[Decimal] = None,
        preco_max: Optional[Decimal] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Any]:
        """Lista safras disponíveis com filtros."""
        pass
    
    @abstractmethod
    def get_safras_produtor(self, produtor_id: int) -> List[Any]:
        """Lista todas as safras de um produtor."""
        pass
    
    @abstractmethod
    def buscar_por_produto(self, produto_nome: str, limite: int = 20) -> List[Any]:
        """Busca safras por nome do produto."""
        pass
    
    @abstractmethod
    def get_safras_recentes(self, limite: int = 10) -> List[Any]:
        """Retorna as safras mais recentes publicadas."""
        pass


class ProdutoRepository(RepositoryBase):
    """
    Interface para acesso a dados de Produtos agrícolas.
    """
    
    @abstractmethod
    def get_by_nome(self, nome: str) -> Optional[Any]:
        """Busca produto pelo nome exato."""
        pass
    
    @abstractmethod
    def buscar_por_nome(self, termo: str) -> List[Any]:
        """Busca produtos por termo ( LIKE %termo% )."""
        pass
    
    @abstractmethod
    def get_produtos_por_categoria(self, categoria: str) -> List[Any]:
        """Lista produtos de uma categoria."""
        pass


# ============================================================
# Exports
# ============================================================

__all__ = [
    'RepositoryBase',
    'UsuarioRepository',
    'TransacaoRepository',
    'SafraRepository',
    'ProdutoRepository',
]
