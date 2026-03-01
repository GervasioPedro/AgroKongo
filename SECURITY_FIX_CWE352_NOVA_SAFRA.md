# Correção CWE-352 - CSRF em produtor.py linhas 160-161

## Vulnerabilidade Identificada
**Localização**: `app/routes/produtor.py` linha 160-161  
**Função**: `nova_safra()`  
**CWE**: CWE-352 (Cross-Site Request Forgery)  
**Severidade**: High

## Problema
A função `nova_safra()` processava requisições POST sem validação CSRF, permitindo criação não autorizada de safras:

```python
# ANTES - Vulnerável
@produtor_bp.route('/nova-safra', methods=['GET', 'POST'])
@login_required
@produtor_required
def nova_safra():
    if not current_user.conta_validada:
        flash('⚠️ A tua conta precisa de ser validada pela administração para publicar.', 'warning')
        return redirect(url_for('produtor.dashboard'))

    if request.method == 'POST':
        # Sem validação CSRF
        try:
            qtd = Decimal(request.form.get('quantidade_kg', '0').replace(',', '.'))
            preco = Decimal(request.form.get('preco_kg', '0').replace(',', '.'))
            # Cria safra sem verificar CSRF
            nova_s = Safra(...)
            db.session.add(nova_s)
            db.session.commit()
```

**Riscos**:
- Atacante poderia criar safras falsas em nome do produtor
- Publicação de produtos com preços manipulados
- Spam de safras na plataforma
- Notificações indevidas para compradores interessados
- Comprometimento da reputação do produtor
- Possível fraude comercial

## Correção Implementada
Adicionada validação CSRF explícita no início do bloco POST:

```python
@produtor_bp.route('/nova-safra', methods=['GET', 'POST'])
@login_required
@produtor_required
def nova_safra():
    if not current_user.conta_validada:
        flash('⚠️ A tua conta precisa de ser validada pela administração para publicar.', 'warning')
        return redirect(url_for('produtor.dashboard'))

    if request.method == 'POST':
        from flask_wtf.csrf import validate_csrf
        from wtforms import ValidationError
        
        # Proteção CSRF
        try:
            validate_csrf(request.form.get('csrf_token'))
        except ValidationError:
            abort(403)
        
        try:
            # Captura com sanitização
            qtd = Decimal(request.form.get('quantidade_kg', '0').replace(',', '.'))
            preco = Decimal(request.form.get('preco_kg', '0').replace(',', '.'))
            # Continua processamento apenas se CSRF válido...
```

## Proteções Adicionadas
1. **Validação CSRF explícita**: `validate_csrf()` verifica token antes de criar safra
2. **Abort 403**: Requisições sem token válido são rejeitadas imediatamente
3. **Proteção de integridade**: Impede criação não autorizada de safras
4. **Proteção de reputação**: Garante que apenas o produtor legítimo publica

## Cenários de Ataque Bloqueados

### Antes (Vulnerável)
- ❌ Atacante cria página maliciosa com form POST para `/nova-safra`
- ❌ Form contém dados de safra falsa (produto, quantidade, preço)
- ❌ Produtor visita página maliciosa enquanto autenticado
- ❌ Form é submetido automaticamente
- ❌ Safra falsa é criada em nome do produtor
- ❌ Compradores interessados recebem notificações
- ❌ Reputação do produtor é comprometida
- ❌ Possível fraude comercial

### Depois (Protegido)
- ✅ Requisição sem token CSRF é rejeitada com HTTP 403
- ✅ Apenas formulários legítimos da aplicação podem criar safras
- ✅ Impossível criar safras via CSRF
- ✅ Reputação do produtor protegida

## Dados Protegidos
- **Produto**: Tipo de safra (milho, feijão, etc.)
- **Quantidade**: Quantidade disponível em kg
- **Preço**: Preço por unidade
- **Observações**: Descrição da safra
- **Imagem**: Foto do produto
- **Notificações**: Alertas para compradores interessados

## Impacto de Segurança
- **Antes**: Atacante poderia criar safras falsas em nome de produtores
- **Depois**: Apenas o produtor legítimo pode criar suas safras
- **Proteção adicional**: Prevenção de spam e fraude comercial

## Proteções Combinadas
1. **CSRF Token**: Previne criação forçada de safras
2. **@login_required**: Requer autenticação
3. **@produtor_required**: Requer tipo de conta 'produtor'
4. **conta_validada**: Requer validação administrativa
5. **Sanitização**: Valores decimais são sanitizados

## Motor de Alertas Protegido
A função também aciona notificações para compradores interessados:
```python
interessados = AlertaPreferencia.query.filter_by(produto_id=nova_s.produto_id).all()
for alerta in interessados:
    db.session.add(Notificacao(
        usuario_id=alerta.usuario_id,
        mensagem=f"🚨 Nova safra de {nova_s.produto.nome} em {current_user.provincia.nome}!",
        link=url_for('mercado.detalhe_safra', id=nova_s.id)
    ))
```

Com CSRF protegido, apenas safras legítimas geram notificações.

## Status
✅ **CORRIGIDO** - Proteção CSRF implementada com sucesso na função nova_safra
🔒 **HIGH** - Esta correção previne criação não autorizada de safras
🛡️ **INTEGRIDADE** - Protege reputação dos produtores e integridade da plataforma
📢 **NOTIFICAÇÕES** - Garante que apenas safras legítimas geram alertas
