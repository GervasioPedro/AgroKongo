# Correção CWE-22: Path Traversal em relatorios.py (Validação Subpasta)

## Vulnerabilidade Identificada
**Ficheiro:** `app/tasks/relatorios.py`  
**Linhas:** 105 (variável subpasta)  
**Severidade:** MÉDIA  
**CWE:** CWE-22 (Path Traversal)

## Descrição da Vulnerabilidade

### Subpasta Hardcoded Sem Validação
- **Problema:** Variável `subpasta` hardcoded como `'relatorios'` mas sem validação whitelist
- **Risco:** Se código for modificado para aceitar `subpasta` como parâmetro, vulnerabilidade seria introduzida
- **Impacto:** Defense in depth - prevenir vulnerabilidades futuras

### Cenário de Risco Futuro
```python
# Se alguém modificar para:
def gerar_relatorio_excel_assincrono(self, admin_id: int, periodo: str = None, subpasta: str = 'relatorios'):
    # Sem validação, subpasta='../../etc' seria aceite
```

## Correção Implementada

### Validação Whitelist de Subpasta

**Antes:**
```python
subpasta = 'relatorios'
# Sem validação
```

**Depois:**
```python
subpasta = 'relatorios'
# Validação whitelist de subpasta
if subpasta not in ['relatorios', 'faturas', 'fotos']:
    raise ValueError("Subpasta inválida")
```

## Camadas de Proteção (Total: 5)

1. ✅ **Whitelist de subpasta**: Apenas valores permitidos
2. ✅ **os.path.basename(periodo)**: Sanitiza período
3. ✅ **os.path.basename(filename)**: Sanitiza filename completo
4. ✅ **os.path.commonpath()**: Valida path final
5. ✅ **ValueError**: Exceções para tentativas de exploração

## Princípio de Defense in Depth

### Por que Validar Subpasta Hardcoded?
1. **Prevenção de regressão**: Se código for modificado no futuro
2. **Documentação**: Deixa claro quais subpastas são válidas
3. **Fail-safe**: Mesmo que hardcoded seja alterado, validação permanece
4. **Best practice**: Validar todos os inputs, mesmo internos

### Whitelist vs Blacklist
- ✅ **Whitelist**: Apenas `['relatorios', 'faturas', 'fotos']` permitidos
- ❌ **Blacklist**: Tentar bloquear `../`, `..\\`, etc. (facilmente contornável)

## Impacto da Correção

### Segurança
- ✅ Previne path traversal através de subpasta
- ✅ Protege contra modificações futuras do código
- ✅ Documentação clara de subpastas válidas

### Manutenibilidade
- ✅ Desenvolvedor futuro sabe quais subpastas são permitidas
- ✅ Erro claro se subpasta inválida for usada
- ✅ Facilita auditoria de segurança

### Compliance
- ✅ Defense in depth (múltiplas camadas de proteção)
- ✅ Fail-safe design (proteção mesmo contra erros internos)
- ✅ Secure by default (validação sempre ativa)

## Exemplo de Proteção

### Tentativa de Modificação Maliciosa
```python
# Desenvolvedor malicioso tenta modificar:
subpasta = '../../etc'

# Validação bloqueia:
if subpasta not in ['relatorios', 'faturas', 'fotos']:
    raise ValueError("Subpasta inválida")  # ✅ Bloqueado
```

### Modificação Legítima Futura
```python
# Desenvolvedor adiciona nova subpasta:
subpasta = 'backups'

# Validação bloqueia até whitelist ser atualizada:
if subpasta not in ['relatorios', 'faturas', 'fotos', 'backups']:  # ← Atualizar aqui
    raise ValueError("Subpasta inválida")
```

## Testes Recomendados

1. **Subpasta Válida:** `'relatorios'` → Aceite ✅
2. **Subpasta Inválida:** `'../../etc'` → ValueError ✅
3. **Subpasta Vazia:** `''` → ValueError ✅
4. **Subpasta None:** `None` → ValueError ✅

## Comparação com Outras Tarefas

### Consistência no Projeto
- **faturas.py**: Usa `subpasta = 'faturas'` (deve adicionar validação similar)
- **relatorios.py**: Usa `subpasta = 'relatorios'` (✅ validação adicionada)
- **uploads.py**: Deve validar subpasta de uploads

## Status
✅ **CORRIGIDO** - Validação whitelist de subpasta adicionada para defense in depth
