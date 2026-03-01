# Tests do AgroKongo

## 📋 Estrutura de Testes

```
tests/
├── __init__.py                 # Configuração base
├── conftest.py                 # Fixtures globais
├── unit/                       # Testes unitários
│   ├── test_models.py          # Modelos (Usuario, Safra, Transacao)
│   ├── test_utils.py           # Utilitários e helpers
│   ├── test_stock.py           # Gestão de stock
│   └── test_financeiro.py      # Cálculos financeiros
├── integration/                # Testes de integração
│   ├── conftest_integration.py # Fixtures específicas
│   ├── test_escrow_flow.py     # Fluxo completo de escrow
│   ├── test_database_integration.py # BD constraints
│   └── test_celery_integration.py # Tasks assíncronas
└── automation/                 # Testes de automação
    ├── test_celery_tasks.py    # Tasks Celery
    └── test_base_task_handler.py # Handler de erros
```

## 🚨 Problemas Identificados

### 1. **Dependências Faltantes**
```bash
# Erro: ModuleNotFoundError: No module named 'flask_login'
pip install -r requirements-test.txt
```

### 2. **Imports Desatualizados**
Os testes ainda usam o modelo antigo. Precisam atualizar para:

**ANTES:**
```python
from app.models import Usuario, Safra, Transacao
```

**DEPOIS:**
```python
from app.models import Usuario, Safra, Transacao
from app.models_carteiras import Carteira, StatusConta
```

### 3. **Status Conta Não Atualizado**
Os testes verificam `conta_validada` mas agora usam `status_conta`.

**ANTES:**
```python
assert usuario.conta_validada == False
```

**DEPOIS:**
```python
assert usuario.status_conta == StatusConta.PENDENTE_VERIFICACAO
```

## 🔧 Como Corrigir

### 1. Instalar Dependências
```bash
pip install -r requirements-test.txt
```

### 2. Atualizar Imports nos Testes
```bash
# Substituir em todos os arquivos de teste
find tests/ -name "*.py" -exec sed -i 's/from app.models import/from app.models import/' {} \;
```

### 3. Atualizar Verificações de Status
```python
# Em test_models.py e outros
from app.models_carteiras import StatusConta

# Substituir verificações
assert usuario.status_conta == StatusConta.PENDENTE_VERIFICACAO
```

### 4. Adicionar Testes do Novo Sistema
```python
# tests/unit/test_cadastro_produtor.py
def test_status_conta_pendente_verificacao(session):
    usuario = Usuario(
        nome="Teste",
        telemovel="912345678",
        tipo="produtor"
    )
    session.add(usuario)
    session.commit()
    
    assert usuario.status_conta == StatusConta.PENDENTE_VERIFICACAO
    assert not usuario.pode_criar_anuncios()

def test_carteira_criada_automaticamente(session, produtor_user):
    carteira = produtor_user.obter_carteira()
    assert carteira is not None
    assert carteira.saldo_disponivel == Decimal('0.00')
```

## 🧪 Executar Testes

### Testes Unitários
```bash
python -m pytest tests/unit/ -v
```

### Testes de Integração
```bash
python -m pytest tests/integration/ -v
```

### Testes de Automação
```bash
python -m pytest tests/automation/ -v
```

### Todos os Testes
```bash
python -m pytest tests/ -v --cov=app
```

## 📊 Cobertura Atual

- **Unitários**: Modelos, utilitários, stock, financeiro
- **Integração**: Fluxo escrow, BD, Celery
- **Automação**: Tasks, handlers, performance

## 🎯 Próximos Passos

1. ✅ Instalar dependências
2. ✅ Atualizar imports
3. ✅ Corrigir verificações de status
4. 🔄 Adicionar testes do cadastro
5. 🔄 Testar sistema OTP
6. 🔄 Validar fluxo completo

## 🚨 Status Atual

**❌ PROBLEMAS:**
- Dependências não instaladas
- Imports desatualizados
- Status não migrado

**✅ FUNCIONAL:**
- Estrutura completa
- Fixtures robustas
- Scripts de execução

**🔧 NECESSÁRIO:**
- Instalar requirements-test.txt
- Atualizar imports nos testes
- Migrar verificações de status
