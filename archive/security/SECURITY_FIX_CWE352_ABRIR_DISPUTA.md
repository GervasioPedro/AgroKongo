# Correção CWE-352 - CSRF em disputas.py linhas 15-16

## Vulnerabilidade Identificada
**Localização**: `app/routes/disputas.py` linha 15-16  
**Função**: `abrir_disputa()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: CRITICAL

## Problema
A função `abrir_disputa()` processava requisições POST sem validação CSRF, permitindo abertura não autorizada de disputas:

```python
# ANTES - Vulnerável CRÍTICO
@disputas_bp.route('/abrir-disputa/<string:trans_uuid>', methods=['GET', 'POST'])
@login_required
def abrir_disputa(trans_uuid):
    transacao = Transacao.query.filter_by(uuid=trans_uuid).first_or_404()
    
    if transacao.comprador_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        # Sem validação CSRF
        try:
            motivo = request.form.get('motivo', '').strip()
            # Cria disputa sem verificar CSRF
            nova_disputa = Disputa(...)
            transacao.status = TransactionStatus.DISPUTA  # Congela valor em escrow
            db.session.add(nova_disputa)
            db.session.commit()
```

**Riscos CRÍTICOS**:
- Atacante poderia abrir disputas falsas em nome de compradores
- Congelamento indevido de valores em escrow
- Bloqueio de transações legítimas
- Sobrecarga do sistema de mediação
- Prejuízo financeiro para produtores (valores congelados)
- Negação de serviço (DoS) via disputas em massa
- Comprometimento da reputação da plataforma

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
@disputas_bp.route('/abrir-disputa/<string:trans_uuid>', methods=['GET', 'POST'])
@login_required
def abrir_disputa(trans_uuid):
    transacao = Transacao.query.filter_by(uuid=trans_uuid).first_or_404()
    
    if transacao.comprador_id != current_user.id:
        abort(403)
    
    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        try:
            motivo = request.form.get('motivo', '').strip()
            # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de criar disputa
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Proteção financeira**: Impede congelamento indevido de valores em escrow
4. **Proteção contra DoS**: Previne abertura em massa de disputas
5. **Integridade do sistema**: Garante que apenas disputas legítimas são criadas

## Cenários de Ataque Bloqueados

### Antes (Vulnerável - CRÍTICO)
- ❌ Atacante identifica UUID de transação (ex: via histórico público)
- ❌ Cria página maliciosa com form POST para `/abrir-disputa/{uuid}`
- ❌ Form contém motivo falso de disputa
- ❌ Comprador visita página maliciosa enquanto autenticado
- ❌ Form é submetido automaticamente
- ❌ Disputa falsa é aberta sem consentimento
- ❌ Transação é bloqueada (status = DISPUTA)
- ❌ Valor fica congelado em escrow
- ❌ Produtor não recebe pagamento
- ❌ Sistema de mediação é sobrecarregado
- ❌ Possível DoS via disputas em massa

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem abrir disputas
- ✅ Impossível abrir disputas via CSRF
- ✅ Valores em escrow protegidos contra congelamento indevido

## Impacto Financeiro

### Congelamento de Valores
Quando uma disputa é aberta:
```python
transacao.status = TransactionStatus.DISPUTA  # Congela valor em escrow
```

**Sem proteção CSRF**:
- Atacante poderia congelar TODOS os valores em escrow
- Produtores não receberiam pagamentos
- Plataforma ficaria inoperante
- Prejuízo financeiro massivo

**Com proteção CSRF**:
- Apenas disputas legítimas congelam valores
- Sistema de escrow funciona corretamente
- Pagamentos fluem normalmente

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

### Camada 3: Autorização
```python
if transacao.comprador_id != current_user.id:
    abort(403)
```
- Apenas comprador da transação pode abrir disputa

### Camada 4: Validação de Prazo (RN05)
```python
pode_abrir, mensagem = disputa_temp.pode_abrir_disputa()
if not pode_abrir:
    flash(mensagem, "warning")
    return redirect(...)
```
- Valida prazo de 24h após previsão de entrega

### Camada 5: Evidência Obrigatória (RN06)
```python
if not motivo or len(motivo) < 20:
    flash("Descreva o motivo com detalhes (mínimo 20 caracteres).", "warning")
    return render_template(...)
```
- Requer descrição detalhada do problema

### Camada 6: Verificação de Duplicidade
```python
if hasattr(transacao, 'disputa') and transacao.disputa:
    flash("Esta transação já possui uma disputa aberta.", "warning")
    return redirect(...)
```
- Impede múltiplas disputas para mesma transação

## Dados Protegidos
- **Transação**: Operação comercial entre comprador e produtor
- **Valor em Escrow**: Dinheiro congelado durante disputa
- **Status da Transação**: Bloqueio/desbloqueio de pagamento
- **Sistema de Mediação**: Fila de disputas para administradores
- **Reputação**: Histórico de disputas dos usuários
- **Evidências**: Documentos e fotos anexadas

## Impacto de Segurança
- **Antes**: Atacante poderia congelar todos os pagamentos da plataforma
- **Depois**: Apenas disputas legítimas são criadas
- **Criticidade**: Esta era uma vulnerabilidade CRÍTICA de sabotagem financeira

## Auditoria e Rastreamento
A função já possui log de auditoria:
```python
db.session.add(LogAuditoria(
    usuario_id=current_user.id,
    acao="ABERTURA_DISPUTA",
    detalhes=f"Comprador abriu disputa para transação {transacao.fatura_ref}...",
    ip=request.remote_addr
))
```

Com CSRF protegido, apenas aberturas legítimas são registradas.

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função abrir_disputa
🔒 **CRITICAL** - Esta correção previne sabotagem financeira e DoS
🛡️ **6 CAMADAS** - CSRF + Autenticação + Autorização + Prazo + Evidência + Duplicidade
💰 **PROTEÇÃO FINANCEIRA** - Previne congelamento indevido de valores em escrow
⚖️ **INTEGRIDADE** - Protege sistema de mediação contra sobrecarga
