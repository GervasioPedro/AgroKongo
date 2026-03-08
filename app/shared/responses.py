"""
Response helpers para padronização das APIs
"""
from flask import jsonify
from typing import Optional, Dict, Any


def success_response(data: Any = None, message: str = "Sucesso", status_code: int = 200) -> tuple:
    """
    Retorna uma resposta de sucesso padronizada
    
    Args:
        data: Dados a serem retornados
        message: Mensagem de sucesso
        status_code: Código HTTP
        
    Returns:
        Tuple (response, status_code)
    """
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    return jsonify(response), status_code


def error_response(message: str = "Erro", status_code: int = 400, errors: Optional[Dict] = None) -> tuple:
    """
    Retorna uma resposta de erro padronizada
    
    Args:
        message: Mensagem de erro
        status_code: Código HTTP
        errors: Detalhes adicionais do erro
        
    Returns:
        Tuple (response, status_code)
    """
    response = {
        'success': False,
        'message': message,
        'errors': errors or {}
    }
    return jsonify(response), status_code


def validation_error(field: str, message: str) -> tuple:
    """
    Retorna um erro de validação específico
    
    Args:
        field: Nome do campo
        message: Mensagem de erro
        
    Returns:
        Tuple (response, status_code)
    """
    return error_response(
        message=f"Erro de validação em {field}",
        status_code=422,
        errors={field: message}
    )


def unauthorized_error(message: str = "Não autorizado") -> tuple:
    """
    Retorna erro de não autorizado
    
    Args:
        message: Mensagem de erro
        
    Returns:
        Tuple (response, status_code)
    """
    return error_response(message=message, status_code=401)


def forbidden_error(message: str = "Acesso proibido") -> tuple:
    """
    Retorna erro de acesso proibido
    
    Args:
        message: Mensagem de erro
        
    Returns:
        Tuple (response, status_code)
    """
    return error_response(message=message, status_code=403)


def not_found_error(message: str = "Recurso não encontrado") -> tuple:
    """
    Retorna erro de recurso não encontrado
    
    Args:
        message: Mensagem de erro
        
    Returns:
        Tuple (response, status_code)
    """
    return error_response(message=message, status_code=404)


def server_error(message: str = "Erro interno do servidor") -> tuple:
    """
    Retorna erro interno do servidor
    
    Args:
        message: Mensagem de erro
        
    Returns:
        Tuple (response, status_code)
    """
    return error_response(message=message, status_code=500)


def conflict_error(message: str = "Conflito de recursos") -> tuple:
    """
    Retorna erro de conflito (409)
    
    Args:
        message: Mensagem de erro
        
    Returns:
        Tuple (response, status_code)
    """
    return error_response(message=message, status_code=409)
