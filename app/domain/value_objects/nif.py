# app/domain/value_objects/nif.py
"""
Value Object NIF - Número de Identificação Fiscal de Angola

Implementa validação de checksum conforme algoritmo oficial angolano.
O NIF angolano tem 10 dígitos, onde o último é o dígito de verificação.

Exemplo: 0012345679 (10 dígitos)
"""
from dataclasses import dataclass
from typing import Optional
import re


class NIFInvalido(Exception):
    """Exceção levantada quando o NIF é inválido."""
    pass


@dataclass(frozen=True)
class NIF:
    """
    Value Object imutável para o NIF angolano.
    
    Regras de validação:
    - Deve ter exatamente 10 dígitos
    - Deve passar no checksum (algoritmo oficial angolano)
    
    Uso:
        nif = NIF("0012345679")
        print(nif.numero)  # "0012345679"
        print(nif.mascarado)  # "001****679"
    """
    _numero: str
    
    def __post_init__(self):
        # Validação imediata na criação
        self._validar()
    
    def _validar(self):
        """Valida o NIF secondo o algoritmo oficial angolano."""
        numero = self._numero
        
        # Verifica se é numérico e tem 10 dígitos
        if not re.match(r'^\d{10}$', numero):
            raise NIFInvalido(
                f"NIF deve ter exatamente 10 dígitos. Recebido: {numero}"
            )
        
        # Algoritmo de validação do NIF angolano
        # Multiplica cada dígito pela sua posição (1-9) e soma
        soma = sum(int(numero[i]) * (10 - i) for i in range(9))
        
        # Calcula o dígito de verificação
        digito_verificacao = (11 - (soma % 11)) % 10
        
        # Compara com o dígito fornecido
        if int(numero[9]) != digito_verificacao:
            raise NIFInvalido(
                f"NIF inválido (checksum falhou). Dígito verificador deveria ser {digito_verificacao}."
            )
    
    @classmethod
    def criar(cls, numero: str) -> 'NIF':
        """
        Factory method para criar um NIF.
        
        Args:
            numero: String contendo o NIF
            
        Returns:
            Instância de NIF se válido
            
        Raises:
            NIFInvalido: Se o NIF não for válido
        """
        # Remove caracteres não numéricos
        numero_limpo = re.sub(r'\D', '', numero)
        return cls(numero_limpo)
    
    @property
    def numero(self) -> str:
        """Retorna o número completo do NIF."""
        return self._numero
    
    @property
    def mascarado(self) -> str:
        """Retorna o NIF mascarado para exibição segura."""
        if len(self._numero) != 10:
            return "**********"
        return f"{self._numero[:3]}*****{self._numero[-3:]}"
    
    @property
    def primeiros_digitos(self) -> str:
        """Retorna os 3 primeiros dígitos (identificador fiscal)."""
        return self._numero[:3]
    
    def __str__(self) -> str:
        return self._numero
    
    def __eq__(self, other) -> bool:
        if isinstance(other, NIF):
            return self._numero == other._numero
        return False
    
    def __hash__(self) -> int:
        return hash(self._numero)


# ============================================================
# compatibilidade com código existente
# ============================================================

def validar_nif_angola(nif: str) -> bool:
    """
    Função de compatibilidade para validar NIF.
    
    Args:
        nif: String contendo o NIF
        
    Returns:
        True se válido, False caso contrário
    """
    try:
        NIF.criar(nif)
        return True
    except NIFInvalido:
        return False


def formatar_nif(nif: Optional[str]) -> str:
    """
    Formata o NIF para exibição segura.
    
    Args:
        nif: String do NIF
        
    Returns:
        NIF mascarado ou string vazia
    """
    if not nif:
        return ""
    try:
        return NIF.criar(nif).mascarado
    except NIFInvalido:
        return "****" * 2
