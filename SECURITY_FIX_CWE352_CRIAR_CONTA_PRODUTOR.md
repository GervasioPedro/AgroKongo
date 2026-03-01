# Correção CWE-352 - CSRF em cadastro_produtor.py linhas 18-19

## Vulnerabilidade Identificada
**Localização**: `app/routes/cadastro_produtor.py` linha 18-19  
**Função**: `criar_conta_produtor()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: High

## Problema
A função `criar_conta_produtor()` processava requisições POST sem validação CSRF:

```python
# ANTES - Vulnerável
@cadastro_bp.route('/criar-conta-produtor', methods=['GET', 'POST'])
def criar_conta_produtor():
    if request.method == 'POST':
        telemovel = request.form.get('telemovel', '').strip()
        # Processa sem validar CSRF
        resultado = gerar_e_enviar_otp(telemovel=telemovel, ...)
```

**Riscos**:
- Atacante poderia forçar envio de OTP para números arbitrários
- Possível DoS através de custos de SMS/WhatsApp
- Criação de contas não autorizadas
- Spam de mensagens OTP para vítimas

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
@cadastro_bp.route('/criar-conta-produtor', methods=['GET', 'POST'])
def criar_conta_produtor():
    """
    Passo 1: Criar Conta como Produtor
    Validação de contato via OTP
    """
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        telemovel = request.form.get('telemovel', '').strip()
        # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de qualquer processamento
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Import de abort**: Adicionado `abort` aos imports do Flask
4. **Proteção contra DoS**: Impede envio forçado de OTP gerando custos

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Atacante cria página maliciosa com form POST para `/criar-conta-produtor`
- ❌ Form contém número de telefone da vítima
- ❌ Vítima visita página maliciosa
- ❌ Form é submetido automaticamente
- ❌ OTP é enviado para vítima sem consentimento
- ❌ Atacante pode gerar custos de SMS repetidamente

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem enviar OTP
- ✅ Proteção contra spam de mensagens OTP
- ✅ Proteção contra DoS via custos de comunicação

## Impacto de Segurança
- **Antes**: Qualquer site malicioso poderia forçar envio de OTP
- **Depois**: Apenas requisições com token CSRF válido são processadas
- **Proteção adicional**: Prevenção de DoS e spam de mensagens

## Fluxo de Cadastro Protegido
Todas as etapas do cadastro agora possuem proteção CSRF:
1. ✅ `criar_conta_produtor()` - Linha 18 (CORRIGIDO)
2. ✅ `validar_otp()` - Linha 59 (CORRIGIDO anteriormente)
3. ✅ `reenviar_codigo()` - Linha 107 (CORRIGIDO anteriormente)
4. ⚠️ `dados_basicos()` - Linha 138 (REQUER VERIFICAÇÃO)
5. ⚠️ `definir_senha()` - Linha 189 (REQUER VERIFICAÇÃO)
6. ⚠️ `dados_financeiros()` - Linha 223 (REQUER VERIFICAÇÃO)

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função criar_conta_produtor
