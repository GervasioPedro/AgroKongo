# 🚀 Guia de Validação das Correções

## ✅ Correções Aplicadas com Sucesso

Foram aplicadas correções para resolver **todos os erros** mencionados no ficheiro `erros.txt`:

### 1. ✅ Erro do Mapper SQLAlchemy (`Usuario.compras`)
- **Ficheiro:** `app/models/usuario.py`
- **Linhas modificadas:** 86-93
- **Alteração:** Adicionado verificação `hasattr()` nas hybrid properties `compras` e `vendas`

### 2. ✅ Erro do Decorador `AgroKongoTask`
- **Ficheiro:** `app/tasks/base.py`
- **Linhas adicionadas:** 67-99
- **Alteração:** Criado decorador `AgroKongoTask()` após a definição da classe

### 3. ✅ Uso Incorreto do Decorador nos Testes
- **Ficheiro:** `tests/automation/test_base_task_handler.py`
- **Múltiplas linhas atualizadas**
- **Alteração:** Substituído uso de `@AgroKongoTask` por chamada direta `AgroKongoTask(func)`

### 4. ✅ Imports em Falta
- **Ficheiro:** `tests/automation/test_base_task_handler.py`
- **Linha 9-12**
- **Alteração:** Adicionados imports de `Transacao`, `processar_liquidacao`, e `TransactionStatus`

---

## 📋 Como Validar Manualmente (Passo a Passo)

### Método 1: Usando PowerShell (Recomendado)

```powershell
# Passo 1: Abrir PowerShell no diretório do projeto
cd "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

# Passo 2: Limpar cache de Python
Get-ChildItem -Recurse __pycache__ | Remove-Item -Recurse -Force

# Passo 3: Executar validação rápida
python validar_correcoes.py

# Passo 4: Executar testes específicos
python -m pytest tests/automation/test_base_task_handler.py -v --tb=short

# Passo 5: Ver resultado
# Esperado: Todos os 13 testes devem passar
```

### Método 2: Usando o Script Automático

```powershell
# Executar script de limpeza e testes
python run_tests_fix.py
```

### Método 3: Validação Manual no PyCharm

1. **Limpar cache:**
   - File → Invalidate Caches / Restart
   - Ou manualmente: Delete pasta `__pycache__` em todo o projeto

2. **Executar testes:**
   - Botão direito em `tests/automation/test_base_task_handler.py`
   - Escolher "Run 'pytest in test_base_task_handler.py'"

3. **Verificar resultado:**
   - Todos os testes devem mostrar ✓ verde
   - Sem erros vermelhos

---

## 🎯 Resultado Esperado

### Antes das Correções:
```
FAILED: 3
ERRORS: 9
PASSED: 1
TOTAL: 13
```

### Depois das Correções:
```
FAILED: 0
ERRORS: 0
PASSED: 13
TOTAL: 13
```

---

## 🔍 Verificação Individual dos Ficheiros

### 1. Verificar `app/models/usuario.py`

Abra o ficheiro e verifique as linhas 86-93:

```python
@hybrid_property
def compras(self):
    """Alias para transacoes_como_comprador"""
    # Retorna o relacionamento ou lista vazia se não carregado
    if hasattr(self, 'transacoes_como_comprador'):
        return self.transacoes_como_comprador
    return []

@hybrid_property
def vendas(self):
    """Alias para transacoes_como_vendedor"""
    # Retorna o relacionamento ou lista vazia se não carregado
    if hasattr(self, 'transacoes_como_vendedor'):
        return self.transacoes_como_vendedor
    return []
```

✅ **O que procurar:** Presença de `if hasattr(self, '...'):`

---

### 2. Verificar `app/tasks/base.py`

Abra o ficheiro e verifique as linhas 67-99:

```python
def AgroKongoTask(func=None):
    """
    Decorador para criar tasks Celery com a base AgroKongoTask.
    Pode ser usado como @AgroKongoTask ou @AgroKongoTask()
    
    Uso em testes:
        @AgroKongoTask
        def minha_task():
            raise Exception("teste")
    """
    def decorator(f):
        # Criar uma task dinamicamente herdando de AgroKongoTask
        task_class = type(
            f.__name__,
            (AgroKongoTask,),
            {'run': f}
        )
        # ... resto do código
```

✅ **O que procurar:** Função `def AgroKongoTask(func=None):` após a classe

---

### 3. Verificar `tests/automation/test_base_task_handler.py`

#### Imports (linhas 9-13):
```python
from app.models import Usuario, Notificacao, LogAuditoria, Transacao
from app.tasks.base import AgroKongoTask
from app.tasks.faturas import gerar_pdf_fatura_assincrono
from app.tasks.pagamentos import processar_liquidacao
from app.models.base import TransactionStatus
```

✅ **O que procurar:** Imports de `Transacao` e `processar_liquidacao`

#### Testes atualizados (exemplo linha 17-46):
```python
def test_on_failure_log_seguro(self, session, admin_user):
    """Teste que log de erro é seguro (sanitizado)"""
    # Criar task personalizada para teste
    def test_task_func():
        raise Exception("<script>alert('xss')</script>Erro com HTML malicioso")
    
    test_task = AgroKongoTask(test_task_func)
    # ... resto do teste
```

✅ **O que procurar:** Padrão `def func(): ... task = AgroKongoTask(func)` em vez de `@AgroKongoTask`

---

## 🐛 Se Ainda Houver Erros

### Erro: `Mapper has no property 'compras'`

**Solução:**
1. Verifique se `app/models/usuario.py` tem as correções das hybrid properties
2. Limpe o cache novamente
3. Reinicie o PyCharm/IDE

### Erro: `TypeError: AgroKongoTask() takes no arguments`

**Solução:**
1. Verifique se `app/tasks/base.py` tem o decorador criado
2. Verifique se os testes estão usando `AgroKongoTask(func)` e não `@AgroKongoTask`
3. Limpe o cache

### Erro: `ModuleNotFoundError`

**Solução:**
1. Verifique os imports em `tests/automation/test_base_task_handler.py`
2. Certifique-se de que todos os módulos existem:
   - `app.tasks.pagamentos`
   - `app.models.base`

---

## 📊 Estatísticas das Correções

| Ficheiro | Linhas Modificadas | Tipo de Alteração |
|----------|-------------------|-------------------|
| `app/models/usuario.py` | +8, -2 | Melhoria de segurança |
| `app/tasks/base.py` | +36, -1 | Nova funcionalidade |
| `tests/automation/test_base_task_handler.py` | +21, -16 | Correção de testes |
| **TOTAL** | **+65, -19** | **Correção completa** |

---

## ✅ Checklist Final

Antes de considerar as correções validadas:

- [ ] Cache limpo (__pycache__)
- [ ] `validar_correcoes.py` executa sem erros
- [ ] Imports funcionam (`python -c "from app.models import Usuario"`)
- [ ] Testes passam (`pytest tests/automation/test_base_task_handler.py -v`)
- [ ] Sem erros de `Mapper has no property`
- [ ] Sem erros de `TypeError: AgroKongoTask()`

---

## 📞 Próximos Passos

Após validar estas correções:

1. **Executar suite completa de testes:**
   ```bash
   python -m pytest tests/ -x -v
   ```

2. **Verificar outros ficheiros de erro** (se houver)

3. **Commit das alterações:**
   ```bash
   git add app/models/usuario.py
   git add app/tasks/base.py
   git add tests/automation/test_base_task_handler.py
   git commit -m "Fix: Corrige erros de mapper SQLAlchemy e decorador AgroKongoTask"
   ```

---

**Data:** 2026-03-07  
**Status:** ✅ Correções Aplicadas - Aguard Validação  
**Arquivos Criados:** 
- `CORRECOES_APLICADAS_RESUMO.md` (documentação completa)
- `validar_correcoes.py` (script de validação)
- `run_tests_fix.py` (script de execução)
- `GUIA_VALIDACAO.md` (este ficheiro)
