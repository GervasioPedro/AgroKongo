# 🚀 GUIA RÁPIDO - INSTALAÇÃO E EXECUÇÃO DE TESTES

## ⚡ INSTALAÇÃO RÁPIDA

### 1. Instalar Dependências de Teste

```bash
# Opção 1: Instalar apenas o necessário (recomendado)
pip install pytest pytest-cov

# Opção 2: Instalar tudo com relatórios HTML
pip install pytest pytest-cov pytest-html

# Opção 3: Instalar todas as dependências (completo)
pip install -r requirements-tests.txt
```

### 2. Verificar Instalação

```bash
pytest --version
```

---

## ▶️ EXECUTAR TESTES

### Windows (PowerShell)

```powershell
# Método 1: Usando script Python (recomendado)
python run_tests.py

# Método 2: Diretamente com pytest
python -m pytest tests/unit/ tests/integration/ tests_framework/ -v --cov=app

# Método 3: Apenas testes unitários
python -m pytest tests/unit/ -v

# Método 4: Arquivo específico
python -m pytest tests/unit/test_criptografia.py -v
```

### Linux/Mac (Bash)

```bash
# Tornar scripts executáveis
chmod +x run_tests.sh
chmod +x run_tests.py

# Executar
./run_tests.sh
# ou
python run_tests.py
```

---

## 📊 VER RELATÓRIOS

Após executar os testes, os relatórios são gerados em:

```bash
# Windows
start reports/test_report.html          # Relatório de testes
start htmlcov/index.html                # Cobertura de código
start reports/coverage.xml              # XML para CI/CD

# Linux
xdg-open reports/test_report.html
xdg-open htmlcov/index.html

# Mac
open reports/test_report.html
open htmlcov/index.html
```

---

## 🔧 COMANDOS ÚTEIS

### Com Flags Especiais

```bash
# Sem verificação de cobertura (mais rápido)
python run_tests.py --no-cov

# Sem relatórios HTML
python run_tests.py --no-html

# Apenas testes unitários
python -m pytest tests/unit/ -v

# Parar na primeira falha
python -m pytest -x

# Mostrar output dos prints
python -m pytest -s

# Timeout maior para testes lentos
python -m pytest --timeout=60
```

### Testes Específicos

```bash
# Por arquivo
python -m pytest tests/unit/test_criptografia.py -v

# Por classe
python -m pytest tests/unit/test_criptografia.py::TestDataEncryption -v

# Por função
python -m pytest tests/unit/test_criptografia.py::TestDataEncryption::test_encrypt_descript_decrypt_sucesso -v

# Por marcador
python -m pytest -m unit
python -m pytest -m integration
python -m pytest -m security
```

---

## 🐛 TROUBLESHOOTING

### Erro: `pytest-html não instalado`

**Solução:**
```bash
pip install pytest-html
```

Ou execute sem HTML:
```bash
python run_tests.py --no-html
```

---

### Erro: `ModuleNotFoundError: No module named 'app'`

**Solução (Windows):**
```powershell
$env:PYTHONPATH="C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"
python run_tests.py
```

**Solução (Linux/Mac):**
```bash
export PYTHONPATH=$(pwd)
python run_tests.py
```

---

### Erro: `Database errors`

**Solução:**
```bash
# Limpar cache do pytest
pytest --cache-clear

# Forçar recriação do banco
rm -f test.db
pytest
```

---

### Erro: `Timeout`

**Solução:**
```bash
# Aumentar timeout
python -m pytest --timeout=300
```

---

## 📈 INTERPRETAR RESULTADOS

### Saída de Sucesso

```
================================================================================
✅ TODOS OS TESTES PASSARAM!
📊 Cobertura de código: 100%
📄 Relatório HTML: file://.../reports/test_report.html
📄 Cobertura HTML: file://.../htmlcov/index.html
================================================================================
```

### Saída de Falha

```
================================================================================
❌ ALGUNS TESTES FALHARAM
📄 Verifique o relatório: file://.../reports/test_report.html
================================================================================
```

---

## 🎯 DICAS DE PERFORMANCE

### Execução Rápida

```bash
# Sem cobertura (mais rápido)
python run_tests.py --no-cov

# Paralelo (se tiver pytest-xdist)
python -m pytest -n auto

# Cache ativado
python -m pytest --cache-dir=.pytest_cache
```

### Execução Completa (Lenta mas Detalhada)

```bash
# Com todos os relatórios
python run_tests.py

# Com benchmark
python -m pytest --benchmark-only
```

---

## 📋 CHECKLIST PRÉ-EXECUÇÃO

```markdown
[ ] Ambiente virtual ativado
[ ] Dependências instaladas (pip install -r requirements-tests.txt)
[ ] Diretório correto (raiz do projeto)
[ ] PYTHONPATH configurado (se necessário)
[ ] Banco de dados de teste disponível
```

---

## 🔗 LINKS ÚTEIS

- **Documentação Completa:** [tests/README_COMPLETO.md](tests/README_COMPLETO.md)
- **Plano de Testes:** [PLANO_TESTES_ROBUSTO_2026.md](PLANO_TESTES_ROBUSTO_2026.md)
- **Requisitos:** [requirements-tests.txt](requirements-tests.txt)

---

**Última atualização:** Março 2026  
**Status:** ✅ VALIDADO E PRONTO PARA USO
