# 🔧 INSTALAÇÃO DE DEPENDÊNCIAS

## Erro Comum: ModuleNotFoundError

Se você encontrou o erro:
```
ModuleNotFoundError: No module named 'flask_talisman'
```

## ✅ SOLUÇÃO RÁPIDA

### Opção 1: Instalar apenas o flask-talisman (Recomendado)
```powershell
pip install flask-talisman
```

### Opção 2: Atualizar todos os requirements
```powershell
# Navegar até o projeto
cd "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

# Instalar todas as dependências
pip install -r requirements.in
```

---

## 🧪 TESTAR SCRIPTS AGORA

Após instalar o flask-talisman:

### Testar validação de índices:
```powershell
python scripts/validar_indices_simples.py
```

### Testar performance (opcional):
```powershell
python scripts/test_query_performance.py
```

---

## 📦 DEPENDÊNCIAS ADICIONAIS PARA TESTES

Se quiser rodar todos os testes:

```powershell
# Instalar pytest
pip install pytest pytest-cov

# Instalar dependências de teste
pip install -r requirements-test.txt
```

---

## ✅ VERIFICAÇÃO

Para verificar se tudo está instalado:

```powershell
python -c "import flask_talisman; print('✅ flask_talisman OK')"
python -c "import sqlalchemy; print('✅ SQLAlchemy OK')"
python -c "import psycopg2; print('✅ PostgreSQL driver OK')"
```

---

## 🐛 PROBLEMAS COMUNS

### Erro: psycopg2 não instala
**Solução:**
```powershell
pip install psycopg2-binary
```

### Erro: Permissão negada no Windows
**Solução:**
```powershell
# Executar como Administrador
# Ou usar --user
pip install --user flask-talisman
```

### Erro: Virtual environment ativado
**Solução:**
```powershell
# Verificar se venv está ativo
# Se não estiver, ativar:
.\venv\Scripts\Activate.ps1  # PowerShell
# ou
venv\Scripts\activate.bat    # CMD

# Depois instalar
pip install flask-talisman
```

---

## 🎯 PRÓXIMOS PASSOS

Após instalar as dependências:

1. ✅ Validar índices: `python scripts/validar_indices_simples.py`
2. ⏭️ Aplicar migration: `flask db upgrade add_strategic_indexes_2026`
3. ⏭️ Validar novamente: `python scripts/validar_indices_simples.py`
4. ⏭️ Testar performance: `python scripts/test_query_performance.py`

---

**Última atualização:** Março 2026  
**Status:** ✅ Requisitos atualizados
