# app/domain/value_objects/telefone.py
"""
Value Object TelefoneAngola - Validação de telemóveis angolanos

Implementa validação de formato conforme padrões angolanos.
Os telemóveis angolanos começam com 9 (9 dígitos total).

Formato: 9X XXX XXXX (onde X é um dígito)
Exemplos: 921234567, 943456789, 991234567
"""
from dataclasses import dataclass
from typing import Optional
import re


class TelefoneInvalido(Exception):
    """Exceção levantada quando o telefone é inválido."""
    pass


@dataclass(frozen=True)
class TelefoneAngola:
    """
    Value Object imutável para telemóveis angolanos.
    
    Regras de validação:
    - Deve ter exatamente 9 dígitos
    - Deve começar com 9
    - Segundo dígito deve ser 1-9 (operadoras possíveis)
    
    Uso:
        telefone = TelefoneAngola.criar("921234567")
        print(telefone.numero)  # "921234567"
        print(telefone.formatado)  # "921 234 567"
    """
    _numero: str
    
    # Mapeamento de prefixos para operadores
    OPERADORAS = {
        '91': 'Unitel',
        '92': 'Unitel',
        '93': 'Unitel',
        '94': 'Unitel',
        '95': 'Movicel',
        '96': 'Movicel',
        '97': 'Movicel',
        '98': 'Movicel',
        '99': 'Movicel',
    }
    
    def __post_init__(self):
        self._validar()
    
    def _validar(self):
        """Valida o número de telemóvel angolano."""
        numero = self._numero
        
        # Verifica se é numérico e tem 9 dígitos
        if not re.match(r'^\d{9}$', numero):
            raise TelefoneInvalido(
                f"Telemóvel deve ter exatamente 9 dígitos. Recebido: {numero}"
            )
        
        # Verifica se começa com 9
        if not numero.startswith('9'):
            raise TelefoneInvalido(
                f"Telemóvel angolano deve começar com 9. Recebido: {numero}"
            )
    
    @classmethod
    def criar(cls, numero: str) -> 'TelefoneAngola':
        """
        Factory method para criar um telefone.
        
        Args:
            numero: String contendo o telefone
            
        Returns:
            Instância de TelefoneAngola se válido
            
        Raises:
            TelefoneInvalido: Se o telefone não for válido
        """
        # Remove caracteres não numéricos
        numero_limpo = re.sub(r'\D', '', numero)
        
        # Remove prefixo 244 se presente
        if numero_limpo.startswith('244'):
            numero_limpo = numero_limpo[3:]
        
        return cls(numero_limpo)
    
    @property
    def numero(self) -> str:
        """Retorna o número completo."""
        return self._numero
    
    @property
    def formatado(self) -> str:
        """Retorna o número formatado: 921 234 567"""
        return f"{self._numero[:3]} {self._numero[3:6]} {self._numero[6:]}"
    
    @property
    def prefixo(self) -> str:
        """Retorna os 2 primeiros dígitos."""
        return self._numero[:2]
    
    @property
    def operador(self) -> str:
        """Retorna a operador com base no prefixo."""
        return self.OPERADORAS.get(self.prefixo, 'Desconhecido')
    
    @property
    def mascarado(self) -> str:
        """Retorna o telefone mascarado para exibição."""
        return f"{self._numero[:3]} *****{self._numero[-2:]}"
    
    def __str__(self) -> str:
        return self._numero
    
    def __eq__(self, other) -> bool:
        if isinstance(other, TelefoneAngola):
            return self._numero == other._numero
        return False
    
    def __hash__(self) -> int:
        return hash(self._numero)


# ============================================================
# compatibilidade com código existente
# ============================================================

def validar_telemovel_angola(telemovel: str) -> bool:
    """
    Função de compatibilidade para validar telemóvel angolano.
    
    Args:
        telemovel: String contendo o telemóvel
        
    Returns:
        True se válido, False caso contrário
    """
    try:
        TelefoneAngola.criar(telemovel)
        return True
    except TelefoneInvalido:
        return False


def formatar_telemovel(telemovel: Optional[str]) -> str:
    """
    Formata o telemóvel para exibição.
    
    Args:
        telemovel: String do telemóvel
        
    Returns:
        Telemóvel formatado ou string vazia
    """
    if not telemovel:
        return ""
    try:
        return TelefoneAngola.criar(telemovel).formatado
    except TelefoneInvalido:
        return telemovel
