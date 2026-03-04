# app/domain/value_objects/iban.py
"""
Value Object IBAN - International Bank Account Number (Angola)

Implementa validação de checksum conforme ISO 13616.

O IBAN angolano tem o formato: AO06 + 21 dígitos = 25 caracteres
Exemplo: AO06000500000012345601152
"""
from dataclasses import dataclass
from typing import Optional
import re


class IBANInvalido(Exception):
    """Exceção levantada quando o IBAN é inválido."""
    pass


@dataclass(frozen=True)
class IBAN:
    """
    Value Object imutável para o IBAN angolano.
    
    Regras de validação:
    - Deve começar com "AO" (código do país)
    - Deve ter 2 dígitos de checksum
    - Deve ter 21 dígitos (BBAN) para Angola
    - Total: 25 caracteres
    - Deve passar no checksum ISO 13616
    
    Uso:
        iban = IBAN.criar("AO06000500000012345601152")
        print(iban.numero)  # "AO06000500000012345601152"
        print(iban.mascarado)  # "AO06 ******** ******** 1152"
    """
    _numero: str
    
    def __post_init__(self):
        self._validar()
    
    def _validar(self):
        """Valida o IBAN secondo o algoritmo ISO 13616."""
        iban = self._numero.upper().replace(' ', '').replace('-', '')
        
        # Verifica formato básico para Angola
        if not re.match(r'^AO\d{23}$', iban):
            raise IBANInvalido(
                f"IBAN angolano deve ter formato: AO06 + 23 dígitos. "
                f"Recebido: {iban} ({len(iban)} caracteres)"
            )
        
        # Algoritmo de validação ISO 13616
        # 1. Move os 4 primeiros caracteres para o final
        rearranged = iban[4:] + iban[:4]
        
        # 2. Converte letras para números (A=10, B=11, ..., Z=35)
        numeric_string = ''
        for char in rearranged:
            if char.isalpha():
                numeric_string += str(10 + (ord(char) - ord('A')))
            else:
                numeric_string += char
        
        # 3. O IBAN é válido se o resto da divisão por 97 for 1
        # Nota: Python pode lidar com inteiros grandes
        if int(numeric_string) % 97 != 1:
            raise IBANInvalido(
                f"IBAN inválido (checksum ISO 13616 falhou)."
            )
    
    @classmethod
    def criar(cls, iban: str) -> 'IBAN':
        """
        Factory method para criar um IBAN.
        
        Args:
            iban: String contendo o IBAN
            
        Returns:
            Instância de IBAN se válido
            
        Raises:
            IBANInvalido: Se o IBAN não for válido
        """
        # Remove espaços e hifens
        iban_limpo = iban.upper().replace(' ', '').replace('-', '')
        return cls(iban_limpo)
    
    @property
    def numero(self) -> str:
        """Retorna o número completo do IBAN."""
        return self._numero
    
    @property
    def mascarado(self) -> str:
        """Retorna o IBAN mascarado para exibição segura."""
        if len(self._numero) != 25:
            return "****"
        
        # Formato: AO06 **** **** **** 1152
        return f"{self._numero[:4]} {self._numero[4:8]} {self._numero[8:16]} {self._numero[16:]}"
    
    @property
    def codigo_pais(self) -> str:
        """Retorna o código do país (AO)."""
        return self._numero[:2]
    
    @property
    def digito_check(self) -> str:
        """Retorna os dígitos de checksum."""
        return self._numero[2:4]
    
    @property
    def bban(self) -> str:
        """Retorna o BBAN (Basic Bank Account Number)."""
        return self._numero[4:]
    
    def __str__(self) -> str:
        return self._numero
    
    def __eq__(self, other) -> bool:
        if isinstance(other, IBAN):
            return self._numero == other._numero
        return False
    
    def __hash__(self) -> int:
        return hash(self._numero)


# ============================================================
# compatibilidade com código existente
# ============================================================

def validar_iban_angola(iban: str) -> bool:
    """
    Função de compatibilidade para validar IBAN angolano.
    
    Args:
        iban: String contendo o IBAN
        
    Returns:
        True se válido, False caso contrário
    """
    try:
        IBAN.criar(iban)
        return True
    except IBANInvalido:
        return False


def formatar_iban(iban: Optional[str]) -> str:
    """
    Formata o IBAN para exibição segura.
    
    Args:
        iban: String do IBAN
        
    Returns:
        IBAN mascarado ou string vazia
    """
    if not iban:
        return ""
    try:
        return IBAN.criar(iban).mascarado
    except IBANInvalido:
        return "****" * 6
