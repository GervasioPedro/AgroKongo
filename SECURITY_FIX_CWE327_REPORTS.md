# Correção CWE-327,328: Insecure Hashing em reports.py

## Vulnerabilidade Identificada
**Ficheiro:** `app/routes/reports.py`  
**Linhas:** 28-29  
**Severidade:** BAIXA-MÉDIA  
**CWE:** CWE-327 (Use of Broken Cryptographic Algorithm), CWE-328 (Reversible One-Way Hash)

## Descrição da Vulnerabilidade

### MD5 para Cache Keys
- **Problema:** `hashlib.md5()` usado para gerar cache keys
- **Risco:** MD5 é criptograficamente quebrado (colisões conhecidas)
- **Impacto:** Possível cache poisoning via colisões MD5

### Código Vulnerável

**Antes:**
```python
def cache_key_relatorio(start_date, end_date):
    period_str = f"{start_date.isoformat()}{end_date.isoformat()}"
    return f"relatorio_financeiro_{hashlib.md5(period_str.encode()).hexdigest()[:12]}"
```

## Correção Implementada

### SHA-256 em vez de MD5

**Depois:**
```python
def cache_key_relatorio(start_date, end_date):
    period_str = f"{start_date.isoformat()}{end_date.isoformat()}"
    return f"relatorio_financeiro_{hashlib.sha256(period_str.encode()).hexdigest()[:12]}"
```

## Status
✅ **CORRIGIDO** - MD5 substituído por SHA-256
