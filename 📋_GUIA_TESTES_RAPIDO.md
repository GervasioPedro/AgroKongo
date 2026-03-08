# 🚀 GUIA RÁPIDO - Executar Testes no PyCharm

## ✅ Status Atual dos Testes

**Testes de Automação:** 13/13 APROVADOS ✅

---

## 📋 Próximos Testes a Executar

### 1. Testes Unitários (Prioridade)

No PyCharm:

```
1. Botão direito em: tests/unit/test_criptografia.py
2. Run 'pytest in test_criptografia.py'
```

**Arquivos importantes:**
- `test_criptografia.py` - Segurança/Criptografia 🔐
- `test_financeiro.py` - Módulo Financeiro 💰
- `test_decorators_tasks.py` - Decorators e Tasks ⚙️
- `test_helpers.py` - Utilitários 🔧
- `test_utils.py` - Utils Gerais

---

### 2. Testes de Integração

```
1. Botão direito em: tests/integration/
2. Run 'pytest in integration/'
```

**Arquivos:**
- `test_cadastro_flow.py` - Fluxo de Cadastro
- `test_escrow_flow.py` - Fluxo de Pagamento (Escrow)
- `test_database_integration.py` - Banco de Dados
- `test_celery_integration.py` - Celery Tasks

---

### 3. Testes do Framework

```
1. Botão direito em: tests_framework/
2. Run 'pytest in tests_framework/'
```

**Arquivos:**
- `test_auth_security.py` - Segurança da Autenticação
- `test_e2e.py` - Testes End-to-End
- `test_financial.py` - Sistema Financeiro
- `test_models.py` - Modelos de Dados

---

## ⚡ Comandos PowerShell

### Executar Todos os Testes

```powershell
# Script completo
.\rodar_todos_testes.ps1

# Ou manualmente
python -m pytest tests/ -v --tb=short
```

### Executar por Categoria

```powershell
# Unitários
python -m pytest tests/unit/ -v

# Integração
python -m pytest tests/integration/ -v

# Automação
python -m pytest tests/automation/ -v

# Framework
python -m pytest tests_framework/ -v
```

### Executar Arquivo Específico

```powershell
# Criptografia
python -m pytest tests/unit/test_criptografia.py -v

# Financeiro
python -m pytest tests/unit/test_financeiro.py -v

# E2E
python -m pytest tests_framework/test_e2e.py -v
```

---

## 🎯 Marcadores Disponíveis

```python
@pytest.mark.unit         # Testes unitários
@pytest.mark.integration  # Testes de integração
@pytest.mark.e2e          # Testes end-to-end
@pytest.mark.slow         # Testes lentos
@pytest.mark.database     # Testes de banco
@pytest.mark.financial    # Testes financeiros
@pytest.mark.security     # Testes de segurança
```

### Executar por Marcador

```powershell
# Apenas segurança
python -m pytest -m security -v

# Apenas financeiro
python -m pytest -m financial -v

# Exceto lentos
python -m pytest -m "not slow" -v
```

---

## 🔍 Debug de Testes

### Ver Output de Prints

```powershell
python -m pytest -s
```

### Parar na Primeira Falha

```powershell
python -m pytest -x
```

### Mostrar Cobertura

```powershell
python -m pytest --cov=app --cov-report=html
start htmlcov/index.html
```

### Ver Relatório HTML

```powershell
start reports/test_report.html
```

---

## 📊 Resultados Esperados

Todos os testes devem mostrar:

```
============================== X passed ==============================
```

**Zero falhas** ✅  
**Zero warnings** ✅  

---

## 🆘 Troubleshooting

### Erro: ModuleNotFoundError

```powershell
# Configurar PYTHONPATH
$env:PYTHONPATH = "."
python -m pytest ...
```

### Erro: Database

```powershell
# Limpar banco de testes
rm test.db
python -m pytest --cache-clear
```

### Erro: Importação

```powershell
# Reinstalar dependências
pip install -r requirements-test.txt --force-reinstall
```

---

## 💡 Dicas PyCharm

1. **Atalhos:**
   - `Ctrl+Shift+F10` - Rodar teste atual
   - `Ctrl+Shift+F9` - Rodar teste com debug
   - `Shift+F6` - Renomear (refatoração segura)

2. **Ícones:**
   - ✅ Verde - Teste passou
   - ❌ Vermelho - Teste falhou
   - ⚪ Cinza - Teste ignorado

3. **Janela "Run":**
   - Ver output completo
   - Filtrar por erro/warning
   - Exportar resultados

---

## 📈 Métricas Alvo

```
✅ Cobertura mínima: 80%
✅ Zero testes falhando
✅ Tempo suite: < 5 minutos
✅ Testes flaky: 0
```

---

## 🎉 Checklist de Validação

- [ ] Testes de automação: 13/13 ✅
- [ ] Testes unitários: Executar
- [ ] Testes de integração: Executar
- [ ] Testes E2E: Executar
- [ ] Cobertura > 80%
- [ ] Zero falhas
- [ ] Relatórios gerados

---

**Boa sorte com os testes! 🚀**
