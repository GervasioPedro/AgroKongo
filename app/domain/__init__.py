# app/domain/__init__.py
# Domain Layer - Domain-Driven Design Structure
# Este módulo organiza a lógica de negócio do AgroKongo

"""
Estrutura DDD (Domain-Driven Design):

├── entities/          # Entidades com identidade
├── value_objects/     # Objetos de valor imutáveis
├── repositories/      # Interfaces abstratas
├── services/          # Serviços de domínio
└── events/            # Eventos de domínio
"""

from app.domain.entities import Usuario, Transacao, Safra, Produto
from app.domain.value_objects import NIF, IBAN, TelefoneAngola
from app.domain.repositories import UsuarioRepository, TransacaoRepository

__all__ = [
    'Usuario',
    'Transacao', 
    'Safra',
    'Produto',
    'NIF',
    'IBAN',
    'TelefoneAngola',
    'UsuarioRepository',
    'TransacaoRepository',
]
