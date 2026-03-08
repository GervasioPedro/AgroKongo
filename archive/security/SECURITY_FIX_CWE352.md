# Correção CWE-352: Cross-Site Request Forgery (CSRF)

## Vulnerabilidade Identificada
**Localização**: `app/routes/admin.py` - Linha 140-141  
**Função**: `confirmar_transferencia()`  
**Severidade**: Alta

## Descrição do Problema
A rota POST `/admin/confirmar-transferencia/<int:id>` não validava o token CSRF, permitindo que um atacante pudesse forjar requisições maliciosas para confirmar transferências bancárias sem autorização.

## Correção Aplicada

### 1. Validação de Token CSRF no Backend
```python
@admin_bp.route('/confirmar-transferencia/<int:id>', methods=['POST'])
@login_required
@admin_required
def confirmar_transferencia(id):
    """O Admin confirma que já fez a transferência bancária para o IBAN do produtor."""
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    venda = Transacao.query.with_for_update().get_or_404(id)
    # ... resto do código
```

### 2. Token CSRF no Template
O template `admin/dashboard.html` já inclui o token CSRF em todos os formulários:
```html
<form action="{{ url_for('admin.liquidar_pagamento', trans_id=d.id) }}" method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <button type="submit" class="btn btn-dark-sharp">
        CONFIRMAR REPASSE
    </button>
</form>
```

## Proteções Implementadas

1. **Validação Explícita**: Token CSRF validado antes de processar qualquer operação financeira
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Flask-WTF**: Proteção CSRF global já configurada em `app/extensions.py`
4. **Templates Seguros**: Todos os formulários POST incluem `{{ csrf_token() }}`

## Outras Rotas Protegidas
As seguintes rotas também possuem proteção CSRF via Flask-WTF:
- `/admin/validar-pagamento/<int:id>`
- `/admin/liquidar-pagamento/<int:trans_id>`
- `/admin/validar-usuario/<int:user_id>`
- `/admin/rejeitar-usuario/<int:user_id>`
- `/admin/rejeitar-pagamento/<int:id>`
- `/admin/usuario/eliminar/<int:user_id>`

## Verificação
Para testar a proteção:
1. Tente enviar uma requisição POST sem o token CSRF
2. O servidor deve retornar HTTP 403 Forbidden
3. Verifique os logs para confirmar a rejeição

## Referências
- CWE-352: https://cwe.mitre.org/data/definitions/352.html
- Flask-WTF CSRF: https://flask-wtf.readthedocs.io/en/stable/csrf.html
- OWASP CSRF: https://owasp.org/www-community/attacks/csrf
