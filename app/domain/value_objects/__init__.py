# app/domain/value_objects/__init__.py
"""
Value Objects - Objetos de Valor Imutáveis
Representam conceitos do domínio sem identidade própria.

Value Objects implementados:
- NIF angolano com validação de checksum
- IBAN angolano com validação de checksum
- TelefoneAngola com validação de formato
"""

from app.domain.value_objects.nif import NIF, NIFInvalido
from app.domain.value_objects.iban import IBAN, IBANInvalido
from app.domain.value_objects.telefone import TelefoneAngola, TelefoneInvalido
from app.domain.value_objects.campos_cifrados import CampoCifradoMixin

__all__ = [
    'NIF',
    'NIFInvalido',
    'IBAN',
    'IBANInvalido',
    'TelefoneAngola',
    'TelefoneInvalido',
    'CampoCifradoMixin',
]
