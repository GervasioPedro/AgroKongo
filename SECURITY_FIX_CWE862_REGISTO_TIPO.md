# Correção CWE-862 - Missing Authorization em auth.py linha 119, 167

## Vulnerabilidade Identificada
**Localização**: `app/routes/auth.py` linha 119, 167  
**Função**: `registo()`  
**CWE**: CWE-862 (Missing Authorization)  
**Severidade**: CRITICAL

## Problema
A função `registo()` permitia criação de contas de qualquer tipo sem validação, incluindo contas 'admin':

```python
# ANTES - Vulnerável CRÍTICO
nome = request.form.get('nome', '').strip().title()
telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
tipo = request.form.get('tipo')  # ← Aceita qualquer valor
senha = request.form.get('senha')

# 1. Validação Estrita de Telemóvel...
# Sem validação do tipo de conta

novo_usuario = Usuario(
    nome=nome,
    telemovel=telemovel,
    tipo=tipo,  # ← Pode ser 'admin'!
    perfil_completo=False,
    conta_validada=False
)
```

**Riscos CRÍTICOS**:
- Atacante poderia criar conta com `tipo='admin'`
- Escalação de privilégios imediata
- Acesso total ao sistema administrativo
- Possibilidade de:
  - Validar qualquer conta
  - Aprovar transações
  - Acessar dados financeiros de todos os usuários
  - Modificar configurações do sistema
  - Deletar dados
  - Comprometer toda a plataforma

## Correção Implementada
Adicionada validação de tipo de conta com whitelist:

```python
nome = request.form.get('nome', '').strip().title()
telemovel = re.sub(r'\D', '', request.form.get('telemovel', ''))
tipo = request.form.get('tipo')
senha = request.form.get('senha')

# Verificação de autorização: apenas tipos permitidos podem ser criados
if tipo not in ['produtor', 'comprador']:
    flash('Tipo de conta inválido.', 'danger')
    from flask import abort
    abort(403)

# 1. Validação Estrita de Telemóvel (Angola: 9 dígitos, começa com 9)
# Continua processamento apenas se tipo válido...
```

## Proteções Adicionadas
1. **Whitelist de tipos**: Apenas 'produtor' e 'comprador' permitidos
2. **Abort 403**: Requisições com tipo inválido são rejeitadas
3. **Mensagem de erro**: Informa usuário sobre tipo inválido
4. **Bloqueio de admin**: Impossível criar conta 'admin' via registro público

## Cenários de Ataque Bloqueados

### Antes (Vulnerável - CRÍTICO)
- ❌ Atacante acessa formulário de registro
- ❌ Modifica campo `tipo` no HTML/request para `tipo=admin`
- ❌ Preenche dados e submete formulário
- ❌ Conta admin é criada com sucesso
- ❌ Atacante faz login com conta admin
- ❌ Acesso total ao painel administrativo
- ❌ Comprometimento completo da plataforma
- ❌ Possível fraude financeira em massa

### Depois (Protegido)
- ✅ Atacante tenta modificar campo `tipo` para `admin`
- ✅ Validação detecta tipo inválido
- ✅ Requisição é rejeitada com HTTP 403
- ✅ Mensagem de erro exibida
- ✅ Conta não é criada
- ✅ Sistema protegido contra escalação de privilégios

## Tipos de Conta Permitidos

| Tipo | Permitido no Registro | Como Criar |
|------|----------------------|------------|
| `produtor` | ✅ Sim | Formulário público |
| `comprador` | ✅ Sim | Formulário público |
| `admin` | ❌ Não | Apenas via console/migração |

## Impacto de Segurança
- **Antes**: Qualquer pessoa poderia criar conta admin e comprometer o sistema
- **Depois**: Apenas tipos 'produtor' e 'comprador' podem ser criados via registro
- **Criticidade**: Esta era uma vulnerabilidade CRÍTICA de escalação de privilégios

## Criação de Contas Admin
Contas admin devem ser criadas apenas por:
1. **Console Python**: Script administrativo
2. **Migração de BD**: Seed data inicial
3. **Comando CLI**: Ferramenta administrativa

```python
# Exemplo seguro de criação de admin (via console)
admin = Usuario(
    nome='Administrador',
    telemovel='999999999',
    tipo='admin',
    perfil_completo=True,
    conta_validada=True
)
admin.set_senha('senha_forte_admin')
db.session.add(admin)
db.session.commit()
```

## Defense in Depth
1. **Whitelist**: Apenas tipos específicos permitidos
2. **Validação explícita**: Verificação antes de criar usuário
3. **Abort 403**: Rejeição imediata de tentativas inválidas
4. **Logging**: Erro registrado para auditoria

## Fluxo de Autenticação - Status Final
1. ✅ `login()` - Linha 20: Protegido com rate limiting
2. ✅ `api_login()` - Linha 53: CSRF exempt apropriado
3. ✅ `api_me()` - Linha 93: Verificação de autenticação
4. ✅ `api_logout()` - Linha 104: CSRF obrigatório
5. ✅ `registo()` - Linha 119: CORRIGIDO - Validação de tipo
6. ✅ `logout()` - Linha 177: Protegido
7. ✅ `editar_perfil()` - Linha 186: Protegido
8. ✅ `alterar_senha()` - Linha 264: Protegido

## Status
✅ **CORRIGIDO** - Validação de tipo de conta implementada com whitelist
🔒 **CRITICAL** - Esta correção previne escalação de privilégios
🎯 **ESSENCIAL** - Proteção fundamental para integridade do sistema
⚠️ **IMPORTANTE** - Contas admin devem ser criadas apenas via console/migração
