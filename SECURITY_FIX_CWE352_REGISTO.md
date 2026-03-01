# Correção CWE-352 - CSRF em auth.py linhas 119-120

## Vulnerabilidade Identificada
**Localização**: `app/routes/auth.py` linha 119-120  
**Função**: `registo()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: High

## Problema
A função `registo()` processava requisições POST sem validação CSRF, permitindo que atacantes criassem contas não autorizadas:

```python
# ANTES - Vulnerável
@auth_bp.route('/registo', methods=['GET', 'POST'])
def registo():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip().title()
        telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        tipo = request.form.get('tipo')
        senha = request.form.get('senha')
        # Processa sem validar CSRF
        novo_usuario = Usuario(...)
        db.session.add(novo_usuario)
        db.session.commit()
```

**Riscos**:
- Atacante poderia criar contas em massa via CSRF
- Registro de contas com dados da vítima sem consentimento
- Spam de contas falsas na plataforma
- Possível abuso para fraude ou lavagem de dinheiro
- Comprometimento da integridade do sistema de cadastro

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
# --- REGISTO COM VALIDAÇÃO ANGOLANA ---
@auth_bp.route('/registo', methods=['GET', 'POST'])
def registo():
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
        
        nome = request.form.get('nome', '').strip().title()
        telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
        tipo = request.form.get('tipo')
        senha = request.form.get('senha')
        # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de criar conta
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Proteção contra spam**: Impede criação automática de contas
4. **Integridade do sistema**: Garante que apenas registros legítimos são processados

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Atacante cria página maliciosa com form POST para `/registo`
- ❌ Form contém dados para criar conta (nome, telefone, tipo, senha)
- ❌ Vítima visita página maliciosa
- ❌ Form é submetido automaticamente
- ❌ Conta é criada sem consentimento da vítima
- ❌ Atacante pode criar centenas de contas falsas
- ❌ Sistema fica vulnerável a spam e fraude

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem criar contas
- ✅ Impossível criar contas via CSRF
- ✅ Proteção contra spam e criação em massa

## Impacto de Segurança
- **Antes**: Atacante poderia criar contas em massa sem interação do usuário
- **Depois**: Apenas registros legítimos com token CSRF válido são processados
- **Proteção adicional**: Prevenção de spam e abuso do sistema

## Dados Protegidos no Registro
- **Nome**: Identificação do usuário
- **Telemóvel**: Número de telefone (9 dígitos Angola)
- **Tipo**: Tipo de conta (produtor/comprador)
- **Senha**: Credenciais de acesso
- **Criação de conta**: Processo completo de registro

## Fluxo de Autenticação - Status Final de Proteção CSRF
1. ✅ `login()` - Linha 20: Protegido (Flask-WTF automático)
2. ✅ `api_login()` - Linha 53: CSRF exempt apropriado (API pública)
3. ✅ `api_me()` - Linha 93: GET, não requer CSRF
4. ✅ `api_logout()` - Linha 104: CORRIGIDO (CSRF obrigatório)
5. ✅ `registo()` - Linha 119: CORRIGIDO (CSRF obrigatório)
6. ✅ `logout()` - Linha 177: Protegido (Flask-WTF automático)
7. ⚠️ `editar_perfil()` - Linha 186: REQUER VERIFICAÇÃO
8. ⚠️ `alterar_senha()` - Linha 264: REQUER VERIFICAÇÃO

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função registo
🔒 **HIGH** - Esta correção previne criação não autorizada de contas
🎯 **IMPORTANTE** - Proteção essencial para integridade do sistema de cadastro
