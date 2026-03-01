# Correção CWE-352 - CSRF em disputas.py linhas 111-112

## Vulnerabilidade Identificada
**Localização**: `app/routes/disputas.py` linha 111-112  
**Função**: `detalhe_disputa()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: CRITICAL

## Problema
A função `detalhe_disputa()` processava requisições POST sem validação CSRF, permitindo resolução não autorizada de disputas por administradores:

```python
# ANTES - Vulnerável CRÍTICO
@disputas_bp.route('/admin/disputa/<int:disputa_id>', methods=['GET', 'POST'])
@login_required
def detalhe_disputa(disputa_id):
    from app.utils.decorators import admin_required
    
    if not admin_required(current_user):
        abort(403)
    
    disputa = Disputa.query.with_for_update().get_or_404(disputa_id)
    
    if request.method == 'POST':
        # Sem validação CSRF
        try:
            decisao = request.form.get('decisao')  # 'comprador' ou 'produtor'
            justificativa = request.form.get('justificativa', '').strip()
            
            # Resolve disputa sem verificar CSRF
            if decisao == 'comprador':
                disputa.resolver_favor_comprador(...)  # Reembolso processado
            elif decisao == 'produtor':
                disputa.resolver_favor_produtor(...)  # Pagamento liberado
            
            db.session.commit()
```

**Riscos CRÍTICOS**:
- Atacante poderia forçar admin a resolver disputas
- Decisões financeiras tomadas sem consentimento
- Reembolsos ou pagamentos processados indevidamente
- Comprometimento da integridade do sistema de mediação
- Perda de confiança na plataforma
- Prejuízo financeiro para compradores ou produtores
- Violação de auditoria e compliance

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
@disputas_bp.route('/admin/disputa/<int:disputa_id>', methods=['GET', 'POST'])
@login_required
def detalhe_disputa(disputa_id):
    from app.utils.decorators import admin_required
    
    if not admin_required(current_user):
        abort(403)
    
    disputa = Disputa.query.with_for_update().get_or_404(disputa_id)
    
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        try:
            decisao = request.form.get('decisao')
            justificativa = request.form.get('justificativa', '').strip()
            # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de resolver disputa
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Proteção financeira**: Impede processamento indevido de reembolsos/pagamentos
4. **Integridade de auditoria**: Garante que apenas decisões legítimas são registradas
5. **Controle de concorrência**: Mantém `with_for_update()` para evitar race conditions

## Cenários de Ataque Bloqueados

### Antes (Vulnerável - CRÍTICO)
- ❌ Atacante identifica ID de disputa (ex: `/admin/disputa/123`)
- ❌ Cria página maliciosa com form POST para resolver disputa
- ❌ Form contém decisão favorável ao atacante
- ❌ Admin visita página maliciosa enquanto autenticado
- ❌ Form é submetido automaticamente
- ❌ Disputa é resolvida sem consentimento do admin
- ❌ Reembolso ou pagamento é processado indevidamente
- ❌ Decisão fraudulenta é registrada em auditoria
- ❌ Prejuízo financeiro para uma das partes

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem resolver disputas
- ✅ Impossível forçar resolução via CSRF
- ✅ Integridade do sistema de mediação protegida

## Impacto Financeiro Crítico

### Decisões Financeiras
Quando uma disputa é resolvida:

**Favor Comprador**:
```python
disputa.resolver_favor_comprador(...)
# - Reembolso processado
# - Valor devolvido ao comprador
# - Produtor não recebe pagamento
```

**Favor Produtor**:
```python
disputa.resolver_favor_produtor(...)
# - Pagamento liberado
# - Valor transferido ao produtor
# - Comprador não recebe reembolso
```

**Sem proteção CSRF**:
- Atacante poderia forçar decisões favoráveis
- Manipulação de resultados financeiros
- Prejuízo direto para uma das partes
- Comprometimento da justiça da plataforma

**Com proteção CSRF**:
- Apenas decisões legítimas do admin são processadas
- Integridade financeira garantida
- Sistema de mediação confiável

## Proteções em Camadas

### Camada 1: CSRF Token
```python
validate_csrf(request.form.get('csrf_token'))
```
- Bloqueia requisições sem token válido

### Camada 2: Autenticação
```python
@login_required
```
- Requer usuário autenticado

### Camada 3: Autorização Admin
```python
if not admin_required(current_user):
    abort(403)
```
- Apenas administradores podem resolver disputas

### Camada 4: Controle de Concorrência (RN07)
```python
disputa = Disputa.query.with_for_update().get_or_404(disputa_id)
```
- Previne race conditions
- Garante que apenas um admin processa por vez

### Camada 5: Validação de Justificativa
```python
if not justificativa or len(justificativa) < 30:
    flash("Forneça justificativa detalhada (mínimo 30 caracteres).", "warning")
    return render_template(...)
```
- Requer justificativa detalhada para auditoria

### Camada 6: Auditoria Completa
```python
# Capturar informações para auditoria
ip_address = request.remote_addr
user_agent = request.headers.get('User-Agent', '')

disputa.resolver_favor_comprador(
    admin_id=current_user.id,
    justificativa=justificativa,
    ip_address=ip_address,
    user_agent=user_agent
)
```
- Registra quem, quando, onde e por quê

## Dados Protegidos
- **Decisão Financeira**: Reembolso ou pagamento
- **Valor em Escrow**: Dinheiro congelado durante disputa
- **Justificativa**: Motivo da decisão administrativa
- **Auditoria**: Registro completo da resolução
- **Reputação**: Histórico de disputas dos usuários
- **Confiança**: Integridade do sistema de mediação

## Impacto de Segurança
- **Antes**: Atacante poderia forçar admin a resolver disputas indevidamente
- **Depois**: Apenas decisões legítimas do admin são processadas
- **Criticidade**: Esta era uma vulnerabilidade CRÍTICA de manipulação financeira

## Auditoria e Compliance
A função já possui auditoria completa:
- Admin ID
- Justificativa detalhada (mínimo 30 caracteres)
- IP address
- User agent
- Timestamp automático

Com CSRF protegido, apenas resoluções legítimas são auditadas.

## Notificações Protegidas
```python
enviar_notificacao_disputa_async.delay(
    disputa_id=disputa.id,
    tipo_notificacao='resolucao',
    decisao=decisao,
    admin_nome=current_user.nome
)
```

Apenas resoluções legítimas geram notificações para as partes.

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função detalhe_disputa
🔒 **CRITICAL** - Esta correção previne manipulação financeira e fraude
🛡️ **6 CAMADAS** - CSRF + Autenticação + Admin + Concorrência + Validação + Auditoria
💰 **PROTEÇÃO FINANCEIRA** - Previne processamento indevido de reembolsos/pagamentos
⚖️ **INTEGRIDADE** - Protege sistema de mediação contra manipulação
📋 **COMPLIANCE** - Garante auditoria apenas de decisões legítimas
