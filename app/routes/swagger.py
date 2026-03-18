"""
Documentação OpenAPI/Swagger para a API AgroKongo.
Geração automática de documentação interativa.
"""
from flask import Blueprint, jsonify, url_for
import os

swagger_bp = Blueprint('swagger', __name__, url_prefix='/api/docs')

# Especificação OpenAPI 3.0
OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "AgroKongo API",
        "description": """
## Marketplace Agrícola Angolano
        
API RESTful para integração com frontend mobile (React Native/Flutter) e web (React).
        
### Funcionalidades Principais:
- **Catálogo de Safras**: Listagem, filtros e detalhes de produtos agrícolas
- **Sistema de Escrow**: Pagamento seguro em custódia
- **Gestão de Usuários**: Produtores e compradores verificados
- **Notificações**: Sistema multi-canal (email, push, in-app)
        
### Autenticação:
Utilize JWT Token no header: `Authorization: Bearer <token>`
        """,
        "version": "1.0.0",
        "contact": {
            "name": "Equipa AgroKongo",
            "email": "dev@agrokongo.ao"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000/api/v1",
            "description": "Desenvolvimento Local"
        },
        {
            "url": "https://api.agrokongo.ao/api/v1",
            "description": "Produção"
        }
    ],
    "tags": [
        {"name": "Safras", "description": "Operações com safras agrícolas"},
        {"name": "Produtos", "description": "Catálogo de produtos"},
        {"name": "Pagamentos", "description": "Processamento financeiro"},
        {"name": "Usuários", "description": "Gestão de usuários"},
        {"name": "Notificações", "description": "Sistema de notificações"}
    ],
    "paths": {},  # Preenchido automaticamente
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        },
        "schemas": {
            "Safra": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "produto": {"type": "string", "example": "Milho Branco"},
                    "categoria": {"type": "string", "example": "Cereais"},
                    "quantidade": {"type": "number", "format": "float", "example": 500.00},
                    "preco_unitario": {"type": "number", "format": "float", "example": 5.00},
                    "preco_total": {"type": "number", "format": "float", "example": 2500.00},
                    "produtor": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "nome": {"type": "string"},
                            "provincia": {"type": "string"},
                            "rating": {"type": "number", "format": "float"}
                        }
                    },
                    "imagem": {"type": "string", "format": "uri"},
                    "observacoes": {"type": "string"}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "error": {"type": "string", "example": "Descrição do erro"}
                }
            },
            "Success": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "message": {"type": "string"},
                    "data": {"type": "object"}
                }
            }
        }
    }
}


@swagger_bp.route('/swagger.json')
def swagger_json():
    """Retorna especificação OpenAPI em JSON."""
    return jsonify(OPENAPI_SPEC)


@swagger_bp.route('/swagger-ui.html')
def swagger_ui():
    """Interface Swagger UI para testar a API."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>AgroKongo API - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: "/api/docs/swagger.json",
                    dom_id: '#swagger-ui',
                    presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
                    layout: "BaseLayout",
                    deepLinking: true,
                    showExtensions: true,
                });
            };
        </script>
    </body>
    </html>
    """


@swagger_bp.route('/')
def redirect_to_swagger():
    """Redireciona para Swagger UI."""
    return swagger_ui()
