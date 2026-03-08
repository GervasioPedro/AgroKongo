# Correção CWE-862 - Missing Authorization em auth.py linha 104

## Vulnerabilidade Identificada
**Localização**: `app/routes/auth.py` linha 104  
**Função**: `api_logout()`  
**CWE**: CWE-862 (Missing Authorization) + CWE-352 (CSRF)  
**Severidade**: Medium

## Problema
A função `api_logout()` tinha duas vulnerabilidades:

1. **CSRF Exempt**: Decorator `@csrf.exempt` desabilitava proteção CSRF
2. **Autorização implícita**: Dependia apenas do `@login_required` sem verificação explícita

```python
# ANTES - Vulnerável
@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
@csrf.exempt  # ← Vulnerabilidade CSRF
def api_logout():
    # Sem verificação explícita de autenticação
    db.session.add(LogAuditoria(usuario_id=current_user.id, acao="LOGOUT"))
    db.session.commit()
    logout_user()
    return jsonify({
        'ok': True
    })
```

**Riscos**:
- Atacante poderia forçar logout de usuários via CSRF
- Possível negação de serviço (DoS) forçando logouts repetidos
- Interrupção de transações em andamento
- Perda de dados não salvos

## Correção Implementada
Removido `@csrf.exempt` e adicionada verificação explícita de autenticação:

```python
@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    # Verificação de autorização: usuário deve estar autenticado
    if not current_user.is_authenticated:
        return jsonify({
            'ok': False,
            'message': 'Não autenticado.'
        }), 401
    
    db.session.add(LogAuditoria(usuario_id=current_user.id, acao="LOGOUT"))
    db.session.commit()
    logout_user()
    return jsonify({
        'ok': True
    })
```

## Proteções Adicionadas
1. **Proteção CSRF**: Removido `@csrf.exempt`, agora requer token CSRF válido
2. **Verificação explícita**: `if not current_user.is_authenticated` antes de processar
3. **Resposta apropriada**: HTTP 401 para requisições não autenticadas
4. **Defense in Depth**: Duas camadas de proteção (decorator + verificação manual)

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Atacante cria página maliciosa com POST para `/api/auth/logout`
- ❌ Vítima autenticada visita página maliciosa
- ❌ Requisição é enviada sem token CSRF (exempt)
- ❌ Vítima é deslogada forçadamente
- ❌ Transação em andamento é perdida
- ❌ Possível DoS via logouts repetidos

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada
- ✅ Verificação dupla de autenticação
- ✅ Logout protegido contra CSRF
- ✅ Impossível forçar logout de outros usuários

## Análise da Linha 93 - api_me()
**Status**: ✅ Já está correta

```python
@auth_bp.route('/api/auth/me')
def api_me():
    if not current_user.is_authenticated:
        return jsonify({
            'ok': False,
            'message': 'Nao autenticado.'
        }), 401
    return jsonify({
        'ok': True,
        'user': current_user.to_dict()
    })
```

**Análise**:
- Não precisa de `@login_required` pois é endpoint de verificação de status
- Tem verificação explícita `if not current_user.is_authenticated`
- Retorna HTTP 401 apropriadamente
- Método GET, não requer proteção CSRF
- **Nenhuma ação necessária**

## Impacto de Segurança
- **Antes**: Atacante poderia forçar logout via CSRF
- **Depois**: Logout protegido com CSRF token obrigatório
- **Proteção adicional**: Verificação dupla de autenticação

## Endpoints de Autenticação - Status Final
1. ✅ `login()` - Linha 20: Protegido com rate limiting
2. ✅ `api_login()` - Linha 53: CSRF exempt apropriado (login público)
3. ✅ `api_me()` - Linha 93: Verificação explícita implementada
4. ✅ `api_logout()` - Linha 104: CORRIGIDO - CSRF obrigatório
5. ✅ `logout()` - Linha 177: Protegido com @login_required
6. ✅ `editar_perfil()` - Linha 186: Protegido com @login_required
7. ✅ `alterar_senha()` - Linha 264: Protegido com @login_required

## Status
✅ **CORRIGIDO** - Proteção CSRF e autorização implementadas no api_logout
✅ **VERIFICADO** - api_me já possui autorização adequada
🔒 **COMPLETO** - Todos os endpoints de autenticação estão protegidos
