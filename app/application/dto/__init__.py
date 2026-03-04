# app/proapplication/dto/__init__.py
"""
Data Transfer Objects (DTOs) - Validação de Dados com Pydantic

Este módulo define os DTOs usados na camada de aplicação para:
- Validação de dados de entrada
- Serialização de respostas
- Documentação automática de APIs

Benefícios:
- Validação automática na entrada
- Serialização para JSON
- Documentação OpenAPI/Swagger
- Type hints para IDE
"""
from app.application.dto.usuario_dto import *
from app.application.dto.transacao_dto import *
from app.application.dto.safra_dto import *

__all__ = []
