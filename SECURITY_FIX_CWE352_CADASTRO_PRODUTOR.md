# Correção CWE-352 - CSRF em cadastro_produtor.py linhas 59-60 e 107

## Vulnerabilidades Identificadas

### 1. Função validar_otp() - Linha 59-60
**Localização**: `app/routes/cadastro_produtor.py` linha 59-60  
**Função**: `validar_otp()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: High

### 2. Função reenviar_codigo() - Linha 107
**Localização**: `app/routes/cadastro_produtor.py` linha 107  
**Função**: `reenviar_codigo()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: High

## Problemas Identificados

### validar_otp()
```python
# ANTES - Vulnerável
if request.method == 'POST':
    otp_form = OTPForm()  # Form criado dentro do POST
    
    if otp_form.validate_on_submit():
        # Processa OTP
```

**Problemas**:
- Form instanciado dentro do bloco POST, não validando CSRF corretamente
- Lógica de validação não bloqueava requisições sem token CSRF válido
- Atacante poderia forçar validação de OTP via CSRF

### reenviar_codigo()
```python
# ANTES - Vulnerável
@cadastro_bp.route('/reenviar-otp', methods=['POST'])
def reenviar_codigo():
    # Sem validação CSRF
    telemovel = session.get('cadastro_telemovel')
    resultado = reenviar_otp(telemovel, canal, request.remote_addr)
```

**Problemas**:
- Nenhuma proteção CSRF implementada
- Atacante poderia forçar reenvio de OTP consumindo recursos (SMS/WhatsApp)
- Possível ataque de negação de serviço (DoS) via custos de SMS

## Correções Implementadas

### validar_otp() - Corrigido
```python
@cadastro_bp.route('/validar-otp', methods=['GET', 'POST'])
def validar_otp():
    from flask import session
    
    telemovel = session.get('cadastro_telemovel')
    
    if not telemovel:
        flash('Sessão expirada. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    otp_form = OTPForm()  # ← Instanciado ANTES do bloco POST
    
    if request.method == 'POST':
        # Proteção CSRF explícita
        if not otp_form.validate_on_submit():
            flash('Requisição inválida. Tente novamente.', 'danger')
            return render_template('cadastro/passo_2_otp.html', otp_form=otp_form)
        
        codigo = otp_form.otp.data
        # Processa validação OTP...
    
    return render_template('cadastro/passo_2_otp.html', otp_form=otp_form)
```

### reenviar_codigo() - Corrigido
```python
@cadastro_bp.route('/reenviar-otp', methods=['POST'])
def reenviar_codigo():
    from flask import session
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    telemovel = session.get('cadastro_telemovel')
    canal = session.get('cadastro_canal', 'whatsapp')
    
    if not telemovel:
        flash('Sessão inválida', 'danger')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    resultado = reenviar_otp(telemovel, canal, request.remote_addr)
    # Processa resultado...
```

## Proteções Adicionadas

### validar_otp()
1. **Form instanciado antes do POST**: Garante validação CSRF correta
2. **Validação explícita**: `validate_on_submit()` bloqueia requisições sem token
3. **Mensagem de erro**: Informa usuário sobre requisição inválida
4. **Retorno seguro**: Renderiza template com form válido

### reenviar_codigo()
1. **Validação CSRF explícita**: `validate_csrf()` com abort(403)
2. **Proteção contra DoS**: Impede reenvio forçado de SMS/WhatsApp
3. **Validação de sessão**: Verifica telemovel antes de processar
4. **Redirecionamento seguro**: Retorna para página apropriada

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Atacante cria página maliciosa com form POST para `/validar-otp`
- ❌ Vítima autenticada visita página maliciosa
- ❌ Form é submetido automaticamente validando OTP sem consentimento
- ❌ Atacante força reenvio de OTP gerando custos de SMS

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Form validation bloqueia submissões maliciosas
- ✅ Reenvio de OTP requer token CSRF válido
- ✅ Proteção contra DoS via custos de SMS/WhatsApp

## Impacto de Segurança
- **Antes**: Atacante poderia validar OTP e reenviar códigos sem consentimento
- **Depois**: Todas as operações POST requerem token CSRF válido
- **Proteção adicional**: Prevenção de DoS via custos de comunicação

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada em ambas as funções
