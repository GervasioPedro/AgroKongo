# app/shared/__init__.py
"""
Shared Module - Utilitários e Componentes Compartilhados

Este módulo contém código reutilizável em todo o projeto:
- Exceções customizadas
- Logging estruturado
- Validadores comuns
- Helpers diversos
"""

from app.shared.exceptions import *
from app.shared.logging import logger, AgroKongoLogger, LogContext

__all__ = [
    # Exceptions
    'AgroKongoException',
    'AutenticacaoException',
    'AutorizacaoException',
    'ValidacaoException',
    'TransacaoException',
    'InfraestruturaException',
    'ConformidadeException',
    # Logging
    'logger',
    'AgroKongoLogger',
    'LogContext',
]
