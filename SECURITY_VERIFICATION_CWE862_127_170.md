# Verificação CWE-862: Missing Authorization em main.py (Linhas 127, 170)

## Status: ✅ AUTORIZAÇÃO JÁ IMPLEMENTADA

**Localização**: `app/routes/main.py` - Linhas 127, 170  
**Funções**: `ler_notificacao()` e `api_wallet()`  
**Data da Verificação**: Atual  

## Resumo Executivo

Ambas as funções nas linhas 127 e 170 **JÁ POSSUEM** verificações de autorização adequadas e não requerem correção adicional.

## Análise das Funções

### Linha 127: `ler_notificacao()` ✅

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
    
    # ... validação de URL e redirect
```

**Proteções Implementadas**:
1. ✅ **Autenticação**: `@login_required`
2. ✅ **Autorização**: Verifica `notif.usuario_id != current_user.id`
3. ✅ **Busca Segura**: `get_or_404()`
4. ✅ **Validação XSS**: Parse de URL
5. ✅ **Resposta Apropriada**: HTTP 403 para acesso não autorizado

**Status**: ✅ **COMPLETAMENTE PROTEGIDA**

### Linha 170: `api_wallet()` ✅

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
1. ✅ **Autenticação**: `@login_required`
2. ✅ **Verificação Dupla**: `if not current_user.is_authenticated`
3. ✅ **Filtragem por Usuário**: `filter_by(usuario_id=current_user.id)`
4. ✅ **Sanitização XSS**: `escape()` em campos de texto
5. ✅ **Whitelist de Tipos**: Valida `tipo` contra lista permitida

**Status**: ✅ **COMPLETAMENTE PROTEGIDA**

## Matriz de Proteção

| Função | Linha | Autenticação | Autorização | Sanitização | Status |
|--------|-------|--------------|-------------|-------------|--------|
| `ler_notificacao()` | 127 | ✅ `@login_required` | ✅ Verifica `usuario_id` | ✅ Parse URL | ✅ Completo |
| `api_wallet()` | 170 | ✅ `@login_required` | ✅ Filtra por `usuario_id` | ✅ `escape()` | ✅ Completo |

## Cenários de Segurança

### Função `ler_notificacao()` (Linha 127)

#### Cenário 1: Acesso à Própria Notificação ✅
```python
# Usuário A (ID: 5) acessa sua notificação
GET /ler-notificacao/123
# notif.usuario_id = 5, current_user.id = 5
# Resultado: 200 OK
```

#### Cenário 2: Acesso à Notificação de Outro ❌
```python
# Usuário A (ID: 5) tenta acessar notificação do Usuário B
GET /ler-notificacao/456
# notif.usuario_id = 10, current_user.id = 5
# Resultado: 403 Forbidden
```

#### Cenário 3: Sem Autenticação ❌
```bash
curl http://localhost:5000/ler-notificacao/123
# Resultado: Redirect para login
```

### Função `api_wallet()` (Linha 170)

#### Cenário 1: Acesso Autenticado ✅
```python
# Usuário A (ID: 5) acessa sua carteira
GET /api/wallet
# Retorna apenas movimentos onde usuario_id = 5
# Resultado: 200 OK com dados do usuário
```

#### Cenário 2: Sem Autenticação ❌
```bash
curl http://localhost:5000/api/wallet
# Resultado: Redirect para login ou 401
```

#### Cenário 3: Tentativa de Bypass ❌
```python
# Mesmo que atacante tente manipular, a query filtra por current_user.id
MovimentacaoFinanceira.query.filter_by(usuario_id=current_user.id)
# Sempre retorna apenas dados do usuário autenticado
```

## Análise de Código Seguro

### `ler_notificacao()` - Camadas de Segurança

```
1. Autenticação: @login_required
   ↓
2. Busca: get_or_404(id)
   ↓
3. Autorização: notif.usuario_id == current_user.id?
   ↓ NÃO → HTTP 403
   ↓ SIM → Continua
4. Atualização: notif.lida = True
   ↓
5. Validação URL: Parse e whitelist
   ↓
6. Redirect: URL validada
```

### `api_wallet()` - Camadas de Segurança

```
1. Autenticação: @login_required
   ↓
2. Verificação Dupla: is_authenticated?
   ↓ NÃO → HTTP 401
   ↓ SIM → Continua
3. Filtragem: filter_by(usuario_id=current_user.id)
   ↓
4. Sanitização: escape() em campos de texto
   ↓
5. Resposta: JSON com dados do usuário
```

## Comparação com Outras Funções

| Função | Autenticação | Autorização | Método |
|--------|--------------|-------------|--------|
| `ler_notificacao()` | ✅ | ✅ Verifica propriedade | Comparação direta |
| `api_wallet()` | ✅ | ✅ Filtra por usuário | Query filter |
| `limpar_notificacoes()` | ✅ | ✅ Filtra por usuário | Query filter |
| `marcar_notificacoes_lidas()` | ✅ | ✅ Filtra por usuário | Query filter |
| `servir_privado()` | ✅ | ✅ Granular | Múltiplas verificações |

**Padrão Consistente**: ✅ Todas as funções seguem o mesmo padrão de segurança

## Proteções Contra OWASP Top 10

| Vulnerabilidade | `ler_notificacao()` | `api_wallet()` | Status |
|-----------------|---------------------|----------------|--------|
| A01:2021 - Broken Access Control | ✅ Verifica `usuario_id` | ✅ Filtra por `usuario_id` | ✅ |
| A03:2021 - Injection | ✅ Parse URL | ✅ `escape()` | ✅ |
| A07:2021 - Authentication Failures | ✅ `@login_required` | ✅ `@login_required` | ✅ |

## Testes de Validação

### Teste 1: `ler_notificacao()` - Acesso Legítimo ✅
```python
# Login como Usuário A
# Notificação pertence ao Usuário A
GET /ler-notificacao/123
# Esperado: 200 OK, notificação marcada como lida
```

### Teste 2: `ler_notificacao()` - Acesso Não Autorizado ❌
```python
# Login como Usuário A
# Notificação pertence ao Usuário B
GET /ler-notificacao/456
# Esperado: 403 Forbidden
```

### Teste 3: `api_wallet()` - Acesso Legítimo ✅
```python
# Login como Usuário A
GET /api/wallet
# Esperado: 200 OK com dados da carteira do Usuário A
```

### Teste 4: `api_wallet()` - Sem Autenticação ❌
```bash
curl http://localhost:5000/api/wallet
# Esperado: Redirect para login ou 401
```

### Teste 5: `api_wallet()` - Isolamento de Dados ✅
```python
# Login como Usuário A (ID: 5)
GET /api/wallet
# Query: MovimentacaoFinanceira.query.filter_by(usuario_id=5)
# Retorna apenas movimentos do Usuário A
# Usuário A NÃO vê movimentos do Usuário B
```

## Boas Práticas Implementadas

### ✅ `ler_notificacao()`

1. **Explicit Authorization**: Verificação clara de propriedade
2. **Fail Secure**: Nega acesso por padrão (403)
3. **Input Validation**: Valida URLs antes de redirecionar
4. **Principle of Least Privilege**: Usuário só acessa suas notificações

### ✅ `api_wallet()`

1. **Defense in Depth**: Múltiplas camadas de verificação
2. **Data Isolation**: Query filtra automaticamente por usuário
3. **Output Encoding**: Sanitiza dados antes de retornar
4. **Whitelist Approach**: Valida tipos permitidos

## Documentação Relacionada

Esta verificação complementa outras análises de segurança:

1. **SECURITY_VERIFICATION_CWE862_120.md** - Verificação anterior de `ler_notificacao()`
2. **SECURITY_FIX_CWE79_XSS.md** - Correção de XSS em `ler_notificacao()`
3. **SECURITY_FIX_CWE862_249.md** - Correção de `perfil_produtor()`
4. **SECURITY_FIX_CWE862_350.md** - Correção de `baixar_fatura()`
5. Este documento - Verificação final de linhas 127 e 170

## Conclusão

### ✅ AMBAS AS FUNÇÕES ESTÃO PROTEGIDAS

#### `ler_notificacao()` (Linha 127)
- ✅ Autenticação obrigatória
- ✅ Verificação de propriedade
- ✅ Validação de URL
- ✅ Resposta apropriada (403)
- **Status**: COMPLETAMENTE SEGURA

#### `api_wallet()` (Linha 170)
- ✅ Autenticação obrigatória
- ✅ Verificação dupla
- ✅ Filtragem por usuário
- ✅ Sanitização de output
- **Status**: COMPLETAMENTE SEGURA

### 🎯 Nível de Segurança: MÁXIMO

Ambas as funções implementam:
- **Defense in Depth**: Múltiplas camadas de proteção
- **Principle of Least Privilege**: Acesso mínimo necessário
- **Fail Secure**: Nega acesso por padrão
- **Data Isolation**: Usuários só acessam seus próprios dados

### ✅ NENHUMA AÇÃO NECESSÁRIA

As implementações atuais atendem e excedem os padrões de segurança da indústria para controle de acesso.

## Referências
- CWE-862: https://cwe.mitre.org/data/definitions/862.html
- OWASP Authorization: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/
- Flask-Login: https://flask-login.readthedocs.io/
- OWASP Top 10 2021: https://owasp.org/Top10/
- Defense in Depth: https://owasp.org/www-community/Defense_in_depth
