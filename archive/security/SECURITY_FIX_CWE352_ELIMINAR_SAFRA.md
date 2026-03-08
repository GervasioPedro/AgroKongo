# Correção CWE-352 - CSRF em produtor.py linhas 257-258

## Vulnerabilidade Identificada
**Localização**: `app/routes/produtor.py` linha 257-258  
**Função**: `eliminar_safra()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: CRITICAL

## Problema
A função `eliminar_safra()` processava requisições POST sem validação CSRF, permitindo eliminação não autorizada de safras:

```python
# ANTES - Vulnerável CRÍTICO
@produtor_bp.route('/safra/eliminar/<int:id>', methods=['POST'])
@login_required
@produtor_required
def eliminar_safra(id):
    # Sem validação CSRF
    safra = Safra.query.get_or_404(id)

    # 1. Verificação de Propriedade
    if safra.produtor_id != current_user.id:
        flash('Não tem permissão para eliminar esta safra.', 'danger')
        return abort(403)
    
    # Elimina safra sem verificar CSRF
    db.session.delete(safra)
    db.session.commit()
```

**Riscos CRÍTICOS**:
- Atacante poderia eliminar safras de produtores
- Perda de dados de produtos publicados
- Interrupção de vendas ativas
- Prejuízo financeiro para produtores
- Sabotagem comercial
- Perda de histórico de produtos

## Correção Implementada
Adicionada validação CSRF explícita no início da função:

```python
@produtor_bp.route('/safra/eliminar/<int:id>', methods=['POST'])
@login_required
@produtor_required
def eliminar_safra(id):
    from flask_wtf.csrf import validate_csrf
    from wtforms import ValidationError
    
    # Proteção CSRF
    try:
        validate_csrf(request.form.get('csrf_token'))
    except ValidationError:
        abort(403)
    
    safra = Safra.query.get_or_404(id)

    # 1. Verificação de Propriedade
    if safra.produtor_id != current_user.id:
        flash('Não tem permissão para eliminar esta safra.', 'danger')
        return abort(403)
    
    # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de eliminar
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Verificação de propriedade**: Apenas dono pode eliminar
4. **Verificação de integridade**: Impede eliminar safras com transações ativas
5. **Proteção contra sabotagem**: Impossível eliminar safras via CSRF

## Cenários de Ataque Bloqueados

### Antes (Vulnerável - CRÍTICO)
- ❌ Atacante identifica ID de safra do produtor (ex: `/safra/123`)
- ❌ Cria página maliciosa com form POST para `/safra/eliminar/123`
- ❌ Produtor visita página maliciosa enquanto autenticado
- ❌ Form é submetido automaticamente
- ❌ Safra é eliminada sem consentimento
- ❌ Produto desaparece da plataforma
- ❌ Vendas ativas são interrompidas
- ❌ Prejuízo financeiro para o produtor

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem eliminar safras
- ✅ Impossível eliminar safras via CSRF
- ✅ Produtos protegidos contra sabotagem

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

### Camada 3: Autorização de Tipo
```python
@produtor_required
```
- Requer tipo de conta 'produtor'

### Camada 4: Verificação de Propriedade
```python
if safra.produtor_id != current_user.id:
    abort(403)
```
- Apenas dono pode eliminar

### Camada 5: Integridade de Negócio
```python
transacoes_ativas = Transacao.query.filter(
    Transacao.safra_id == id,
    Transacao.status != 'cancelada'
).first()

if transacoes_ativas:
    flash('Não é possível eliminar uma safra com pedidos ativos...')
    return redirect(...)
```
- Impede eliminar safras com vendas ativas

## Impacto de Segurança
- **Antes**: Atacante poderia eliminar safras causando prejuízo financeiro
- **Depois**: Apenas o produtor legítimo pode eliminar suas safras
- **Criticidade**: Esta era uma vulnerabilidade CRÍTICA de sabotagem comercial

## Dados Protegidos
- **Safra**: Produto publicado pelo produtor
- **Histórico**: Registro de produtos oferecidos
- **Transações**: Vendas vinculadas à safra
- **Reputação**: Histórico comercial do produtor
- **Receita**: Vendas ativas não são interrompidas

## Impacto Financeiro Potencial
- **Sem proteção**: Atacante poderia eliminar todas as safras de um produtor
- **Com proteção**: Impossível eliminar safras via CSRF
- **Prejuízo evitado**: Perda de vendas, reputação e histórico

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função eliminar_safra
🔒 **CRITICAL** - Esta correção previne sabotagem comercial e perda de dados
🛡️ **5 CAMADAS** - CSRF + Autenticação + Autorização + Propriedade + Integridade
💰 **PROTEÇÃO FINANCEIRA** - Previne prejuízo para produtores
