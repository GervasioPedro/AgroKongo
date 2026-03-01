# Correção CWE-352 - CSRF em cadastro_produtor.py linhas 178-179

## Vulnerabilidade Identificada
**Localização**: `app/routes/cadastro_produtor.py` linha 178-179  
**Função**: `definir_senha()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: Critical

## Problema
A função `definir_senha()` processava requisições POST sem validação CSRF, permitindo que atacantes definissem senhas para contas em processo de cadastro:

```python
# ANTES - Vulnerável
@cadastro_bp.route('/definir-senha', methods=['GET', 'POST'])
def definir_senha():
    from flask import session
    
    dados = session.get('cadastro_dados')
    
    if not dados:
        flash('Dados básicos não preenchidos. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    if request.method == 'POST':
        senha = request.form.get('senha', '').strip()
        # Processa sem validar CSRF
        session['cadastro_senha'] = senha
```

**Riscos Críticos**:
- Atacante poderia definir senha para conta de vítima em processo de cadastro
- Comprometimento total da conta antes mesmo de ser criada
- Vítima perderia acesso à própria conta
- Atacante teria controle total sobre conta financeira (IBAN, documentos)

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
@cadastro_bp.route('/definir-senha', methods=['GET', 'POST'])
def definir_senha():
    """
    Passo 4: Segurança (Password)
    PIN de 4 a 6 dígitos (mais fácil de memorizar)
    """
    from flask import session
    
    dados = session.get('cadastro_dados')
    
    if not dados:
        flash('Dados básicos não preenchidos. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        senha = request.form.get('senha', '').strip()
        confirmar_senha = request.form.get('confirmar_senha', '').strip()
        # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de processar senha
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Proteção de credenciais**: Impede definição não autorizada de senha
4. **Segurança da conta**: Garante que apenas o proprietário define a senha

## Cenários de Ataque Bloqueados

### Antes (Vulnerável - CRÍTICO)
- ❌ Vítima inicia cadastro e preenche dados básicos
- ❌ Atacante cria página maliciosa com form POST para `/definir-senha`
- ❌ Form contém senha escolhida pelo atacante
- ❌ Vítima visita página maliciosa enquanto tem sessão ativa
- ❌ Form é submetido automaticamente
- ❌ Senha da conta é definida pelo atacante
- ❌ Vítima completa cadastro mas não consegue fazer login
- ❌ Atacante tem acesso total à conta com IBAN e documentos da vítima

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem definir senha
- ✅ Vítima mantém controle total sobre suas credenciais
- ✅ Conta protegida contra takeover durante cadastro

## Impacto de Segurança
- **Antes**: Atacante poderia assumir controle de contas em cadastro
- **Depois**: Apenas o proprietário legítimo pode definir senha
- **Criticidade**: Esta era uma das vulnerabilidades mais graves do sistema

## Fluxo de Cadastro - Status de Proteção CSRF
1. ✅ `criar_conta_produtor()` - Linha 18 (CORRIGIDO)
2. ✅ `validar_otp()` - Linha 59 (CORRIGIDO)
3. ✅ `reenviar_codigo()` - Linha 107 (CORRIGIDO)
4. ⚠️ `dados_basicos()` - Linha 138 (REQUER VERIFICAÇÃO)
5. ✅ `definir_senha()` - Linha 178 (CORRIGIDO - CRÍTICO)
6. ⚠️ `dados_financeiros()` - Linha 223 (REQUER VERIFICAÇÃO)

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função definir_senha
🔒 **CRÍTICO** - Esta correção previne takeover de contas durante cadastro
