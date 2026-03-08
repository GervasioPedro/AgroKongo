# Correções Aplicadas - Erros dos Testes

## Data: 2026-03-07

### Resumo dos Erros Corrigidos

Foram identificados e corrigidos os seguintes erros no arquivo `erros.txt`:

---

## 1. ✅ Campo `status_conta` faltando no modelo Usuario

**Erro:** `TypeError: 'status_conta' is an invalid keyword argument for Usuario`

**Causa:** O modelo `Usuario` não tinha o campo `status_conta` definido, mas os testes estavam tentando usar este parâmetro.

**Solução:** Adicionado o campo `status_conta` ao modelo `Usuario`:

```python
# Arquivo: app/models/usuario.py
status_conta = db.Column(db.String(50), default=StatusConta.PENDENTE_VERIFICACAO)
```

**Arquivos modificados:**
- `app/models/usuario.py` (linha 72)

---

## 2. ✅ Fixtures `auth_comprador_client` e `auth_client` faltando

**Erro:** `fixture 'auth_comprador_client' not found` / `fixture 'auth_client' not found`

**Causa:** Os fixtures não estavam definidos no conftest.py

**Solução:** Adicionados os fixtures faltantes:

```python
# Arquivo: tests/conftest.py

@pytest.fixture
def auth_client(client, admin_user):
    """Cliente autenticado para testes - versão genérica"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def auth_comprador_client(client, comprador_user):
    """Cliente autenticado como comprador para testes"""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(comprador_user.id)
        sess['_fresh'] = True
    return client
```

**Arquivos modificados:**
- `tests/conftest.py` (linhas 305-320)

---

## 3. ✅ Fixture `mock_redis` faltando

**Erro:** `fixture 'mock_redis' not found`

**Causa:** Fixture necessário para testes que usam Redis não estava definido.

**Solução:** Criado mock do Redis:

```python
# Arquivo: tests/conftest.py

@pytest.fixture
def mock_redis(monkeypatch):
    """Mock do Redis para testes"""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        def set(self, key, value, ex=None):
            self.data[key] = value
        
        def get(self, key):
            return self.data.get(key)
        
        def delete(self, key):
            if key in self.data:
                del self.data[key]
        
        def exists(self, key):
            return key in self.data
    
    mock_redis_instance = MockRedis()
    
    def mock_redis_client(*args, **kwargs):
        return mock_redis_instance
    
    monkeypatch.setattr('redis.Redis', mock_redis_client)
    return mock_redis_instance
```

**Arquivos modificados:**
- `tests/conftest.py` (linhas 334-361)

---

## 4. ✅ Parâmetro incorreto na função `_criar_usuario_produtor`

**Erro:** `TypeError: _criar_usuario_produtor() got an unexpected keyword argument 'financeiros'`

**Causa:** A função espera o parâmetro `iban` diretamente, não um dict `financeiros`.

**Solução:** Atualizadas todas as chamadas da função nos testes:

```python
# Antes (incorreto):
usuario = _criar_usuario_produtor(
    telemovel=telemovel,
    dados=dados_basicos,
    senha=senha,
    financeiros=dados_financeiros  # ❌ Incorreto
)

# Depois (correto):
usuario = _criar_usuario_produtor(
    telemovel=telemovel,
    dados=dados_basicos,
    senha=senha,
    iban=dados_financeiros['iban']  # ✅ Correto
)
```

**Arquivos modificados:**
- `tests/integration/test_cadastro_flow.py` (linhas 64, 188, 332)

---

## 5. ✅ Fixtures de setup faltando

**Erro:** `fixture 'setup_produtor_data' not found` / `fixture 'setup_transacao_data' not found`

**Causa:** Fixtures auxiliares não estavam definidos.

**Solução:** Adicionados fixtures de setup:

```python
# Arquivo: tests/conftest.py

@pytest.fixture
def setup_produtor_data(session, produtor_user):
    """Setup de dados do produtor para testes"""
    # Cria província, município e atualiza produtor
    
@pytest.fixture
def setup_transacao_data(session, produtor_user, comprador_user, produto):
    """Setup de transação para testes"""
    # Cria safra e transação para testes
    
@pytest.fixture
def setup_comprador_transacoes(session, comprador_user, produtor_user, safra_ativa):
    """Setup de transações para testes de comprador"""
    # Cria transação para testes
```

**Arquivos modificados:**
- `tests/conftest.py` (linhas 279-332)

---

## 6. ✅ Erro de contexto da aplicação Flask

**Erro:** `RuntimeError: Working outside of application context`

**Causa:** O teste estava tentando usar `url_for()` fora do contexto da aplicação Flask.

**Solução:** Adicionado `app.app_context()` no teste:

```python
# Arquivo: tests/integration/test_produtor_routes.py

def test_produtor_required_nao_autenticado_acesso(self, app, client):
    with app.app_context():
        response = client.get(url_for('produtor.api_dashboard_produtor'))
        # ... verificações
```

**Arquivos modificados:**
- `tests/integration/test_produtor_routes.py` (linha 174-180)

---

## 7. ✅ Unique constraint failed na carteira

**Erro:** `sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: carteiras.usuario_id`

**Causa:** O teste estava tentando criar uma carteira com `usuario_id=1` que já poderia existir no banco de dados de testes.

**Solução:** Usar um ID único que não conflite com outros testes:

```python
# Arquivo: tests/integration/test_fim_de_ciclo.py

carteira = Carteira(
    usuario_id=99999,  # ID único para evitar conflito
    saldo_disponivel=Decimal('100.00'),
    saldo_bloqueado=Decimal('0.00')
)
```

**Arquivos modificados:**
- `tests/integration/test_fim_de_ciclo.py` (linha 609)

---

## Quantidade de Erros Corrigidos

- **Total de erros no arquivo:** 71 (12 failed + 59 errors)
- **Erros corrigidos nesta sessão:** 7 tipos de erros críticos
  1. Campo status_conta faltando
  2. Fixtures auth_comprador_client e auth_client
  3. Fixture mock_redis
  4. Parâmetro incorreto _criar_usuario_produtor
  5. Fixtures setup_produtor_data e setup_transacao_data
  6. Contexto aplicação Flask
  7. Unique constraint carteira
- **Erros esperados após correção:** Múltiplos erros relacionados a `status_conta` devem ser resolvidos

---

## Próximos Passos

1. Executar os testes novamente para validar as correções
2. Verificar se existem outros erros residuais
3. Corrigir eventuais novos erros que possam surgir

---

## Comandos para Validação

```bash
# Executar testes de cadastro
python -m pytest tests/integration/test_cadastro_flow.py -v

# Executar testes de comprador
python -m pytest tests/integration/test_comprador_routes.py -v

# Executar todos os testes de integração
python -m pytest tests/integration/ -v
```

---

## Observações Importantes

1. **Campo status_conta:** Agora é um campo oficial no modelo Usuario, com valor default `StatusConta.PENDENTE_VERIFICACAO`

2. **Fixtures de autenticação:** Os fixtures `auth_client` e `auth_comprador_client` simulam login através da sessão do Flask

3. **Mock do Redis:** Implementação simplificada para testes que não dependem de Redis real

4. **Função _criar_usuario_produtor:** Assinatura correta é `(telemovel, dados, senha, iban)`

---

**Status:** ✅ Correções aplicadas com sucesso
**Próxima ação:** Validar execução dos testes
