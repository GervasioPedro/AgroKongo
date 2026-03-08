# Correção CWE-20, CWE-79, CWE-80: Cross-Site Scripting (XSS)

## Vulnerabilidades Identificadas
**Localização**: `app/routes/main.py` - Linhas 117-118  
**Funções Afetadas**: 
- `ler_notificacao()` (linha ~117)
- `api_wallet()` (linha ~145)

**Severidade**: Alta

## Descrição dos Problemas

### 1. CWE-79/80 - Linha 117-118: Open Redirect via XSS
**Problema**: A função `ler_notificacao()` redirecionava para `notif.link` sem validação, permitindo:
- URLs maliciosas com `javascript:` scheme
- Redirecionamento para sites externos de phishing
- Injeção de código JavaScript via URL

**Exemplo de Ataque**:
```python
# Atacante cria notificação com link malicioso
notif.link = "javascript:alert('XSS')"
notif.link = "http://phishing-site.com/fake-login"
notif.link = "data:text/html,<script>alert('XSS')</script>"
```

### 2. CWE-20 - Validação de Input Inadequada
**Problema**: Dados de `MovimentacaoFinanceira` eram retornados sem sanitização na API `/api/wallet`, permitindo XSS se o campo `descricao` ou `tipo` contivesse HTML/JavaScript malicioso.

### 3. Lógica de Autenticação Fraca
**Problema**: A rota `/api/wallet` retornava dados fictícios para usuários não autenticados em vez de negar acesso.

## Correções Aplicadas

### 1. Imports de Segurança Adicionados
```python
from urllib.parse import urlparse
from markupsafe import escape
```

### 2. Validação de URL em `ler_notificacao()` (LINHAS 117-118)
```python
@main_bp.route('/ler-notificacao/<int:id>')
@login_required
def ler_notificacao(id):
    """Gere a leitura de notificações e redirecionamento seguro."""
    notif = Notificacao.query.get_or_404(id)

    # Segurança: Impedir que um utilizador leia notificações de outro
    if notif.usuario_id != current_user.id:
        abort(403)

    notif.lida = True
    db.session.commit()

    # Validação de URL para prevenir XSS
    destino = url_for('main.dashboard')
    if notif.link:
        parsed = urlparse(notif.link)
        # Apenas permite URLs relativas (sem scheme/netloc) ou do mesmo domínio
        if not parsed.scheme and not parsed.netloc:
            destino = notif.link
        elif parsed.scheme in ['http', 'https']:
            # Permite apenas se for URL interna da aplicação
            if parsed.netloc == request.host:
                destino = notif.link
    
    return redirect(destino)
```

**Proteções Implementadas**:
- Parse da URL com `urlparse()` para análise de componentes
- Permite apenas URLs relativas (sem scheme/netloc)
- Bloqueia schemes maliciosos (`javascript:`, `data:`, `file:`)
- Permite URLs absolutas apenas do mesmo domínio (`request.host`)
- Fallback seguro para `main.dashboard` se URL for inválida

### 3. Sanitização de Dados em `api_wallet()`
```python
@main_bp.route('/api/wallet')
@login_required
def api_wallet():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401

    carteira = current_user.obter_carteira()

    movimentos = MovimentacaoFinanceira.query.filter_by(usuario_id=current_user.id) \
        .order_by(MovimentacaoFinanceira.data_movimentacao.desc()).limit(20).all()

    movimentos_json = []
    for m in movimentos:
        movimentos_json.append({
            'id': str(m.id),
            'tipo': escape(m.tipo) if m.tipo in ['credito', 'debito', 'escrow'] else 'outro',
            'valorKz': float(m.valor),
            'descricao': escape(m.descricao or ''),
            'createdAtISO': m.data_movimentacao.isoformat() if m.data_movimentacao else None
        })

    return jsonify({
        'resumo': {
            'saldoDisponivelKz': float(carteira.saldo_disponivel),
            'saldoEscrowKz': float(getattr(carteira, 'saldo_bloqueado', 0) or 0),
            'pendentes': Transacao.query.filter_by(comprador_id=current_user.id, status=TransactionStatus.PENDENTE).count()
        },
        'movimentos': movimentos_json
    })
```

**Proteções Implementadas**:
- Requer autenticação com `@login_required`
- Retorna HTTP 401 para usuários não autenticados
- Sanitiza `tipo` e `descricao` com `escape()` do MarkupSafe
- Valida `tipo` contra whitelist de valores permitidos
- Remove dados fictícios de teste

## Técnicas de Proteção Implementadas

### 1. URL Validation (Open Redirect Prevention)
```python
parsed = urlparse(notif.link)

# Permite URLs relativas
if not parsed.scheme and not parsed.netloc:
    destino = notif.link

# Permite URLs absolutas apenas do mesmo domínio
elif parsed.scheme in ['http', 'https']:
    if parsed.netloc == request.host:
        destino = notif.link
```

### 2. HTML/JavaScript Escaping
```python
from markupsafe import escape

# Sanitiza strings antes de retornar na API
'descricao': escape(m.descricao or '')
'tipo': escape(m.tipo)
```

### 3. Whitelist Validation
```python
# Apenas valores conhecidos são permitidos
tipo = escape(m.tipo) if m.tipo in ['credito', 'debito', 'escrow'] else 'outro'
```

### 4. Autenticação Obrigatória
```python
@login_required
def api_wallet():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 401
```

## Cenários de Ataque Bloqueados

### 1. JavaScript Injection
```python
# ANTES (Vulnerável)
notif.link = "javascript:alert(document.cookie)"
# Executaria código JavaScript

# DEPOIS (Protegido)
# URL é rejeitada, redireciona para dashboard
```

### 2. Open Redirect para Phishing
```python
# ANTES (Vulnerável)
notif.link = "http://evil-site.com/fake-login"
# Redirecionaria para site malicioso

# DEPOIS (Protegido)
# Apenas URLs do mesmo domínio são permitidas
```

### 3. Data URI XSS
```python
# ANTES (Vulnerável)
notif.link = "data:text/html,<script>alert('XSS')</script>"
# Executaria código malicioso

# DEPOIS (Protegido)
# Scheme 'data:' é bloqueado
```

### 4. XSS via API Response
```python
# ANTES (Vulnerável)
m.descricao = "<script>alert('XSS')</script>"
# Retornaria script sem sanitização

# DEPOIS (Protegido)
# Retorna: "&lt;script&gt;alert('XSS')&lt;/script&gt;"
```

## Impacto das Correções

### Segurança
✅ Previne XSS via open redirect  
✅ Bloqueia schemes maliciosos (javascript:, data:, file:)  
✅ Permite apenas URLs internas da aplicação  
✅ Sanitiza dados de API antes de retornar  
✅ Valida tipos de dados contra whitelist  
✅ Requer autenticação em endpoints sensíveis  

### Funcionalidade
✅ URLs relativas internas continuam funcionando  
✅ Redirecionamentos legítimos mantidos  
✅ Fallback seguro para dashboard  
✅ API retorna dados reais apenas para autenticados  
✅ Mensagens de erro apropriadas  

## Testes Recomendados

### 1. Teste de JavaScript Injection
```python
# Criar notificação com link malicioso
notif = Notificacao(
    usuario_id=1,
    mensagem="Teste",
    link="javascript:alert('XSS')"
)
# Deve redirecionar para dashboard, não executar JS
```

### 2. Teste de Open Redirect
```python
notif.link = "http://evil-site.com"
# Deve redirecionar para dashboard, não para site externo
```

### 3. Teste de URL Relativa Válida
```python
notif.link = "/comprador/dashboard"
# Deve redirecionar corretamente
```

### 4. Teste de XSS na API
```bash
# Inserir descrição maliciosa
curl -X POST /api/movimentacao \
  -d '{"descricao": "<script>alert(1)</script>"}'

# Verificar que retorna escapado
curl /api/wallet
# Deve retornar: "&lt;script&gt;alert(1)&lt;/script&gt;"
```

### 5. Teste de Autenticação
```bash
curl http://localhost:5000/api/wallet
# Deve retornar 401 Unauthorized
```

## Outras Proteções Existentes

O Flask já fornece proteções automáticas:
- **Jinja2 Auto-escaping**: Templates escapam HTML por padrão
- **Flask-WTF CSRF**: Proteção contra CSRF já configurada
- **Content-Type Headers**: JSON responses têm Content-Type correto

## Recomendações Adicionais

### 1. Content Security Policy (CSP)
Adicionar em `app/__init__.py`:
```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

### 2. X-Content-Type-Options
```python
response.headers['X-Content-Type-Options'] = 'nosniff'
```

### 3. Validação de Notificações na Criação
Adicionar validação quando notificações são criadas:
```python
def criar_notificacao(usuario_id, mensagem, link=None):
    if link:
        parsed = urlparse(link)
        if parsed.scheme and parsed.scheme not in ['http', 'https']:
            link = None  # Rejeita schemes inválidos
    
    notif = Notificacao(usuario_id=usuario_id, mensagem=mensagem, link=link)
    db.session.add(notif)
```

## Referências
- CWE-20: https://cwe.mitre.org/data/definitions/20.html
- CWE-79: https://cwe.mitre.org/data/definitions/79.html
- CWE-80: https://cwe.mitre.org/data/definitions/80.html
- OWASP XSS: https://owasp.org/www-community/attacks/xss/
- OWASP Open Redirect: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
- MarkupSafe: https://markupsafe.palletsprojects.com/
