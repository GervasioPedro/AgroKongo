# Correção CWE-352 - CSRF em cadastro_produtor.py linhas 214-215

## Vulnerabilidade Identificada
**Localização**: `app/routes/cadastro_produtor.py` linha 214-215  
**Função**: `dados_financeiros()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: CRITICAL

## Problema
A função `dados_financeiros()` processava requisições POST sem validação CSRF, permitindo que atacantes manipulassem dados financeiros e documentos de identidade durante o cadastro:

```python
# ANTES - Vulnerável CRÍTICO
@cadastro_bp.route('/dados-financeiros', methods=['GET', 'POST'])
def dados_financeiros():
    from flask import session
    
    dados = session.get('cadastro_dados')
    senha = session.get('cadastro_senha')
    telemovel = session.get('cadastro_telemovel')
    
    if not dados or not senha or not telemovel:
        flash('Dados incompletos. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    if request.method == 'POST':
        iban = request.form.get('iban', '').strip().upper()
        bi_file = request.files.get('bi_file')
        # Processa sem validar CSRF
        session['cadastro_financeiros'] = {
            'iban': iban,
            'bi_path': bi_path
        }
        # Cria usuário com dados manipulados
        usuario = _criar_usuario_produtor(...)
```

**Riscos CRÍTICOS**:
- Atacante poderia substituir IBAN da vítima pelo seu próprio
- Upload de documento de identidade falso/malicioso
- Criação de conta com dados financeiros do atacante
- Vítima perderia todos os pagamentos (iriam para IBAN do atacante)
- Fraude financeira e roubo de identidade
- Lavagem de dinheiro usando identidade da vítima

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
@cadastro_bp.route('/dados-financeiros', methods=['GET', 'POST'])
def dados_financeiros():
    """
    Passo 5: Dados Financeiros (KYC)
    IBAN e upload do Bilhete de Identidade
    """
    from flask import session
    
    dados = session.get('cadastro_dados')
    senha = session.get('cadastro_senha')
    telemovel = session.get('cadastro_telemovel')
    
    if not dados or not senha or not telemovel:
        flash('Dados incompletos. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        iban = request.form.get('iban', '').strip().upper()
        bi_file = request.files.get('bi_file')
        # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de processar dados financeiros
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Proteção financeira**: Impede manipulação não autorizada de IBAN
4. **Proteção de identidade**: Impede upload de documentos falsos
5. **Integridade KYC**: Garante que apenas o proprietário define dados financeiros

## Cenários de Ataque Bloqueados

### Antes (Vulnerável - CRÍTICO)
- ❌ Vítima completa cadastro até definir senha
- ❌ Atacante cria página maliciosa com form POST para `/dados-financeiros`
- ❌ Form contém IBAN do atacante e documento falso
- ❌ Vítima visita página maliciosa enquanto tem sessão ativa
- ❌ Form é submetido automaticamente com multipart/form-data
- ❌ IBAN do atacante é associado à conta da vítima
- ❌ Documento falso é enviado para validação
- ❌ Conta é criada com dados financeiros do atacante
- ❌ Todos os pagamentos da vítima vão para conta do atacante
- ❌ Fraude financeira e lavagem de dinheiro

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem definir IBAN
- ✅ Upload de documentos protegido contra manipulação
- ✅ Vítima mantém controle total sobre dados financeiros
- ✅ Integridade do processo KYC garantida

## Impacto de Segurança
- **Antes**: Atacante poderia roubar todos os pagamentos da vítima
- **Depois**: Apenas o proprietário legítimo pode definir dados financeiros
- **Criticidade**: Esta era a vulnerabilidade MAIS GRAVE do sistema

## Dados Financeiros Protegidos
- **IBAN**: Conta bancária para receber pagamentos (AO06 + 21 dígitos)
- **Bilhete de Identidade**: Documento oficial para validação KYC
- **Criação de conta**: Processo completo de cadastro com dados sensíveis

## Impacto Financeiro Potencial
- **Sem proteção**: Atacante poderia desviar TODOS os pagamentos
- **Com proteção**: Impossível manipular dados financeiros via CSRF
- **Conformidade**: Proteção essencial para regulamentação financeira

## Fluxo de Cadastro - Status FINAL de Proteção CSRF
1. ✅ `criar_conta_produtor()` - Linha 18 (CORRIGIDO)
2. ✅ `validar_otp()` - Linha 59 (CORRIGIDO)
3. ✅ `reenviar_codigo()` - Linha 107 (CORRIGIDO)
4. ✅ `dados_basicos()` - Linha 128 (CORRIGIDO)
5. ✅ `definir_senha()` - Linha 178 (CORRIGIDO)
6. ✅ `dados_financeiros()` - Linha 214 (CORRIGIDO - CRÍTICO)

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função dados_financeiros
🔒 **CRITICAL** - Esta correção previne fraude financeira e roubo de identidade
🎯 **COMPLETO** - Todo o fluxo de cadastro agora está protegido contra CSRF

## Resumo de Segurança
O fluxo completo de cadastro de produtor agora possui proteção CSRF em todas as 6 etapas:
- ✅ Envio de OTP protegido
- ✅ Validação de OTP protegida
- ✅ Reenvio de OTP protegido
- ✅ Dados básicos protegidos
- ✅ Definição de senha protegida (CRÍTICO)
- ✅ Dados financeiros protegidos (CRÍTICO)

**Nenhuma etapa do cadastro pode ser manipulada via CSRF.**
