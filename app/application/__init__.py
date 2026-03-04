ior # app/application/__init__.py
"""
Application Layer - Casos de Uso e CQRS

Este módulo implementa a camada de aplicação seguindo o padrão CQRS
(Command Query Responsibility Segregation).

Estrutura:
├── commands/    # Operações de escrita
├── queries/     # Operações de leitura
└── dto/        # Data Transfer Objects
"""
from app.application.commands import *
from app.application.queries import *
from app.application.dto import *

__all__ = []
