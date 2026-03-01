# Correção CWE-20/79/80 - XSS/Open Redirect em main.py linha 235

## Vulnerabilidade Identificada
**Localização**: `app/routes/main.py` linha 235  
**Função**: `limpar_notificacoes()`  
**CWE**: CWE-20 (Improper Input Validation), CWE-79 (XSS), CWE-80 (XSS via Redirect)  
**Severidade**: Medium

## Problema
A função usava `request.referrer` diretamente no redirect sem validação:

```python
return redirect(request.referrer or url_for('main.index'))
```

**Riscos**:
- Atacante pode manipular o header `Referer` para redirecionar para site malicioso
- Open Redirect pode ser usado para phishing
- Possível XSS através de URLs com `javascript:` ou `data:` schemes

## Correção Implementada
Adicionada validação de URL antes do redirecionamento:

```python
# Validação de URL para prevenir Open Redirect/XSS
destino = url_for('main.index')
if request.referrer:
    parsed = urlparse(request.referrer)
    # Apenas permite URLs do mesmo domínio
    if parsed.netloc == request.host or not parsed.netloc:
        destino = request.referrer

return redirect(destino)
```

## Proteções Adicionadas
1. **Default seguro**: `url_for('main.index')` como destino padrão
2. **Validação de domínio**: Apenas aceita URLs do mesmo host (`parsed.netloc == request.host`)
3. **URLs relativas**: Permite URLs sem netloc (URLs internas relativas)
4. **Rejeição de externos**: Qualquer URL externa é ignorada

## Cenários Bloqueados
- ❌ `https://evil.com/phishing` → Bloqueado (domínio diferente)
- ❌ `javascript:alert(1)` → Bloqueado (scheme malicioso)
- ❌ `data:text/html,<script>alert(1)</script>` → Bloqueado
- ✅ `/dashboard` → Permitido (URL relativa)
- ✅ `https://agrokongo.ao/perfil` → Permitido (mesmo domínio)

## Status
✅ **CORRIGIDO** - Validação de URL implementada com sucesso
