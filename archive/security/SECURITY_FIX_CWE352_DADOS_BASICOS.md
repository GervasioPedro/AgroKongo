# Correção CWE-352 - CSRF em cadastro_produtor.py linhas 128-129

## Vulnerabilidade Identificada
**Localização**: `app/routes/cadastro_produtor.py` linha 128-129  
**Função**: `dados_basicos()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: High

## Problema
A função `dados_basicos()` processava requisições POST sem validação CSRF, permitindo que atacantes manipulassem dados pessoais durante o cadastro:

```python
# ANTES - Vulnerável
@cadastro_bp.route('/dados-basicos', methods=['GET', 'POST'])
def dados_basicos():
    from flask import session
    
    telemovel = session.get('cadastro_telemovel')
    
    if not telemovel:
        flash('Sessão expirada. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    provincias = Provincia.query.order_by(Provincia.nome).all()
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        # Processa sem validar CSRF
        session['cadastro_dados'] = {
            'nome': nome,
            'provincia_id': int(provincia_id),
            'municipio_id': int(municipio_id),
            'principal_cultura': principal_cultura
        }
```

**Riscos**:
- Atacante poderia alterar nome completo da vítima
- Manipulação de província e município
- Alteração de principal cultura (dados de negócio)
- Dados incorretos armazenados na conta final
- Possível fraude de identidade

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
@cadastro_bp.route('/dados-basicos', methods=['GET', 'POST'])
def dados_basicos():
    """
    Passo 3: Dados Básicos
    Nome Completo, Província, Município, Principal Cultura
    """
    from flask import session
    
    telemovel = session.get('cadastro_telemovel')
    
    if not telemovel:
        flash('Sessão expirada. Comece novamente.', 'warning')
        return redirect(url_for('cadastro.criar_conta_produtor'))
    
    provincias = Provincia.query.order_by(Provincia.nome).all()
    
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        nome = request.form.get('nome', '').strip()
        provincia_id = request.form.get('provincia_id')
        municipio_id = request.form.get('municipio_id')
        principal_cultura = request.form.get('principal_cultura', '').strip()
        # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de processar dados
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Proteção de identidade**: Impede manipulação não autorizada de dados pessoais
4. **Integridade de dados**: Garante que apenas o proprietário define seus dados

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Vítima inicia cadastro e valida OTP
- ❌ Atacante cria página maliciosa com form POST para `/dados-basicos`
- ❌ Form contém nome falso, província/município incorretos
- ❌ Vítima visita página maliciosa enquanto tem sessão ativa
- ❌ Form é submetido automaticamente
- ❌ Dados básicos são alterados pelo atacante
- ❌ Conta é criada com informações falsas
- ❌ Possível fraude de identidade ou localização

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem definir dados
- ✅ Vítima mantém controle total sobre suas informações
- ✅ Integridade dos dados pessoais garantida

## Impacto de Segurança
- **Antes**: Atacante poderia manipular dados pessoais durante cadastro
- **Depois**: Apenas o proprietário legítimo pode definir seus dados
- **Proteção adicional**: Prevenção de fraude de identidade

## Dados Protegidos
- **Nome completo**: Identificação do produtor
- **Província/Município**: Localização geográfica (importante para logística)
- **Principal cultura**: Dados de negócio (tipo de produção)

## Fluxo de Cadastro - Status de Proteção CSRF
1. ✅ `criar_conta_produtor()` - Linha 18 (CORRIGIDO)
2. ✅ `validar_otp()` - Linha 59 (CORRIGIDO)
3. ✅ `reenviar_codigo()` - Linha 107 (CORRIGIDO)
4. ✅ `dados_basicos()` - Linha 128 (CORRIGIDO)
5. ✅ `definir_senha()` - Linha 178 (CORRIGIDO)
6. ⚠️ `dados_financeiros()` - Linha 223 (REQUER VERIFICAÇÃO)

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função dados_basicos
🔒 **HIGH** - Esta correção previne manipulação de dados pessoais durante cadastro
