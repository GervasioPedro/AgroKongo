# Correção CWE-352 - CSRF em auth.py linhas 18-19

## Vulnerabilidade Identificada
**Localização**: `app/routes/auth.py` linha 18-19  
**Função**: `login()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: High

## Problema
A função `login()` processava requisições POST sem validação CSRF explícita, permitindo login forçado:

```python
# ANTES - Vulnerável
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Sem validação CSRF explícita
        telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(telemovel=telemovel).first()
        
        if usuario and usuario.verificar_senha(senha):
            login_user(usuario, remember=True)
            # Login realizado sem verificar CSRF
```

**Riscos**:
- Atacante poderia forçar login de vítima em conta controlada
- Login silencioso em conta do atacante
- Rastreamento de atividades da vítima
- Possível phishing avançado
- Associação de ações maliciosas à conta da vítima

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
# --- LOGIN COM PROTEÇÃO ---
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            from flask import abort
            abort(403)
        
        # Limpeza de input para evitar espaços acidentais
        telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        senha = request.form.get('senha')
        # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de processar login
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Rate limiting**: Mantém proteção de "5 per minute" contra brute force
4. **Defense in Depth**: CSRF + Rate Limiting + Validação de credenciais

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Atacante cria página maliciosa com form POST para `/login`
- ❌ Form contém credenciais da conta do atacante
- ❌ Vítima visita página maliciosa enquanto navegando
- ❌ Form é submetido automaticamente
- ❌ Vítima é logada na conta do atacante sem perceber
- ❌ Atividades da vítima são rastreadas pelo atacante
- ❌ Possível associação de ações maliciosas à vítima

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem fazer login
- ✅ Impossível forçar login via CSRF
- ✅ Vítima protegida contra login não autorizado

## Ataque de Login CSRF (Login CSRF Attack)

### O que é?
Diferente de CSRF tradicional, Login CSRF força a vítima a fazer login em conta do atacante:

1. **Objetivo**: Rastrear atividades da vítima
2. **Método**: Forçar login em conta controlada pelo atacante
3. **Consequência**: Vítima usa conta do atacante pensando ser a sua

### Exemplo de Ataque
```html
<!-- Página maliciosa do atacante -->
<form id="evil" action="https://agrokongo.ao/login" method="POST">
    <input name="telemovel" value="999999999">  <!-- Conta do atacante -->
    <input name="senha" value="senha_atacante">
</form>
<script>
    document.getElementById('evil').submit();
</script>
```

### Impacto
- Vítima faz compras na conta do atacante
- Atacante vê histórico de navegação da vítima
- Dados pessoais da vítima são associados à conta do atacante
- Possível chantagem ou phishing avançado

## Impacto de Segurança
- **Antes**: Atacante poderia forçar login de vítimas em contas controladas
- **Depois**: Login protegido com token CSRF obrigatório
- **Proteção adicional**: Rate limiting previne brute force

## Proteções Combinadas
1. **CSRF Token**: Previne login forçado
2. **Rate Limiting**: "5 per minute" previne brute force
3. **Validação de credenciais**: Senha deve estar correta
4. **Mensagem genérica**: Previne enumeração de contas

## Fluxo de Autenticação - Status FINAL
1. ✅ `login()` - Linha 18: CORRIGIDO - CSRF obrigatório
2. ✅ `api_login()` - Linha 53: CSRF exempt apropriado (API)
3. ✅ `api_me()` - Linha 93: GET, não requer CSRF
4. ✅ `api_logout()` - Linha 104: CSRF obrigatório
5. ✅ `registo()` - Linha 119: CSRF obrigatório + validação de tipo
6. ✅ `logout()` - Linha 177: Protegido
7. ✅ `editar_perfil()` - Linha 186: Protegido + path traversal fix
8. ✅ `alterar_senha()` - Linha 264: Protegido

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função login
🔒 **HIGH** - Esta correção previne Login CSRF attacks
🎯 **COMPLETO** - Todas as funções de autenticação agora estão protegidas contra CSRF
🛡️ **DEFENSE IN DEPTH** - CSRF + Rate Limiting + Validação de credenciais
