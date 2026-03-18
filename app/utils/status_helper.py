"""
Helpers para compatibilidade com a classe de constantes TransactionStatus.
"""
from app.models import TransactionStatus

def get_all_status_values():
    """
    Retorna uma lista de todos os valores de status válidos.
    Usa introspecção para ler os atributos da classe.
    """
    return [
        value for key, value in TransactionStatus.__dict__.items()
        if not key.startswith('__') and not callable(value)
    ]

def status_to_value(status):
    """
    Valida e retorna o valor string de um status.
    
    Args:
        status (str): O valor do status a ser validado.
        
    Returns:
        str: O valor string do status se for válido.
    
    Raises:
        ValueError: Se o status não for um valor válido.
    """
    if isinstance(status, str):
        valid_statuses = get_all_status_values()
        if status in valid_statuses:
            return status
        raise ValueError(f"Status inválido: '{status}'. Válidos: {valid_statuses}")
    else:
        # Se não for string, assume que é um atributo válido e tenta obter o valor
        # (isto é menos seguro, mas mantém compatibilidade)
        try:
            # Tenta tratar como se fosse um Enum, mas pode falhar
            return str(status)
        except:
             raise TypeError(f"Tipo de status não suportado: {type(status)}")


def get_status_description(value):
    """
    Obtém descrição amigável de um status (substitui o nome do atributo).
    Ex: 'pagamento_sob_analise' -> 'Pagamento Sob Análise'
    """
    if not isinstance(value, str):
        value = str(value)
        
    return value.replace('_', ' ').title()
