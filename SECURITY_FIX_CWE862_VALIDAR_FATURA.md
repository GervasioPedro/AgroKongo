# Correção CWE-862 - Missing Authorization em mercado.py linhas 124, 134

## Vulnerabilidade Identificada
**Localização**: `app/routes/mercado.py` linha 124, 134  
**Função**: `validar_fatura()`  
**CWE**: CWE-862 (Missing Authorization)  
**Severidade**: High

## Problema
A função `validar_fatura()` expunha TODOS os dados da transação para QUALQUER pessoa com o código da fatura:

```python
# ANTES - Vulnerável
@mercado_bp.route('/validar-fatura/<code>')
def validar_fatura(code):
    """Verifica a autenticidade de uma fatura via QR Code."""
    venda = Transacao.query.filter(Transacao.fatura_ref == code).first()

    if not venda:
        return render_template('mercado/validar_fatura.html', erro="Fatura não encontrada.")

    # Expõe TODOS os dados para QUALQUER pessoa
    return render_template('mercado/validar_fatura.html', venda=venda)
```

**Riscos**:
- Exposição de dados pessoais (nomes, telefones, endereços)
- Exposição de dados financeiros (valores, IBANs)
- Exposição de dados comerciais (quantidades, preços)
- Violação de privacidade de compradores e produtores
- Possível uso para fraude ou phishing
- Enumeração de transações da plataforma
- Violação de GDPR/LGPD

## Dados Sensíveis Expostos

### Informações Pessoais
- Nome completo do comprador
- Nome completo do produtor
- Telefone do comprador
- Telefone do produtor
- Endereço de entrega
- Província e município

### Informações Financeiras
- Valor total da transação
- Preço por unidade
- IBAN do produtor
- Comissão da plataforma
- Valor líquido do vendedor

### Informações Comerciais
- Quantidade comprada
- Produto específico
- Histórico de transações
- Padrões de compra

## Correção Implementada
Adicionada verificação de autorização com dois níveis de acesso:

```python
@mercado_bp.route('/validar-fatura/<code>')
def validar_fatura(code):
    """Verifica a autenticidade de uma fatura via QR Code."""
    venda = Transacao.query.filter(Transacao.fatura_ref == code).first()

    if not venda:
        return render_template('mercado/validar_fatura.html', erro="Fatura não encontrada.")

    # Verificação de autorização: apenas partes envolvidas ou admin podem ver detalhes completos
    if current_user.is_authenticated:
        # Usuário autenticado: verifica se é parte da transação ou admin
        if current_user.id in [venda.comprador_id, venda.vendedor_id] or current_user.tipo == 'admin':
            # Acesso completo aos detalhes
            return render_template('mercado/validar_fatura.html', venda=venda, acesso_completo=True)
    
    # Acesso público: apenas validação básica (sem dados sensíveis)
    dados_publicos = {
        'fatura_ref': venda.fatura_ref,
        'status': venda.status,
        'data_criacao': venda.data_criacao,
        'valida': True
    }
    return render_template('mercado/validar_fatura.html', dados_publicos=dados_publicos, acesso_completo=False)
```

## Proteções Adicionadas

### Nível 1: Acesso Completo (Autorizado)
**Quem tem acesso**:
- Comprador da transação
- Vendedor (produtor) da transação
- Administradores do sistema

**O que veem**:
- Todos os dados da transação
- Informações pessoais completas
- Valores financeiros
- Histórico completo

### Nível 2: Acesso Público (Não Autorizado)
**Quem tem acesso**:
- Qualquer pessoa com o código da fatura
- Usuários não autenticados
- Terceiros

**O que veem (APENAS)**:
- Referência da fatura (código)
- Status da transação
- Data de criação
- Confirmação de validade

**O que NÃO veem**:
- ❌ Nomes de comprador/vendedor
- ❌ Valores financeiros
- ❌ Quantidades
- ❌ Endereços
- ❌ Telefones
- ❌ IBANs
- ❌ Produtos específicos

## Cenários de Uso

### Cenário 1: Comprador Verifica Própria Fatura
```python
# Comprador autenticado acessa sua fatura
# current_user.id == venda.comprador_id
# Resultado: Acesso completo ✅
```

### Cenário 2: Produtor Verifica Venda
```python
# Produtor autenticado acessa fatura de sua venda
# current_user.id == venda.vendedor_id
# Resultado: Acesso completo ✅
```

### Cenário 3: Admin Audita Transação
```python
# Admin verifica qualquer fatura
# current_user.tipo == 'admin'
# Resultado: Acesso completo ✅
```

### Cenário 4: Terceiro Verifica Autenticidade
```python
# Pessoa não autenticada ou terceiro
# Escaneia QR code da fatura
# Resultado: Apenas validação básica ✅
# Vê: Código, status, data, validade
# NÃO vê: Dados pessoais, valores, detalhes
```

### Cenário 5: Usuário Tenta Acessar Fatura de Outro
```python
# Usuário autenticado mas não é parte da transação
# current_user.id != comprador_id e != vendedor_id
# Resultado: Apenas validação básica ✅
```

## Caso de Uso Legítimo: Validação Pública

### Por que permitir acesso público?
O QR code na fatura serve para:
1. **Verificar autenticidade**: Confirmar que a fatura é real
2. **Prevenir fraude**: Detectar faturas falsificadas
3. **Transparência**: Mostrar que a transação existe

### O que é seguro mostrar publicamente?
- ✅ Código da fatura (já está no QR code)
- ✅ Status (confirma que existe)
- ✅ Data (contexto temporal)
- ✅ Validade (autenticidade)

### O que NÃO deve ser público?
- ❌ Identidade das partes
- ❌ Valores financeiros
- ❌ Detalhes comerciais
- ❌ Informações de contato

## Impacto de Segurança
- **Antes**: Qualquer pessoa com código da fatura via TODOS os dados sensíveis
- **Depois**: Apenas partes autorizadas veem dados completos, público vê apenas validação
- **Privacidade**: Protege dados pessoais e financeiros conforme GDPR/LGPD

## Compliance e Privacidade

### GDPR/LGPD
- ✅ Minimização de dados: Apenas dados necessários são expostos
- ✅ Controle de acesso: Apenas partes autorizadas veem dados completos
- ✅ Propósito legítimo: Validação pública sem expor dados sensíveis
- ✅ Segurança: Proteção contra acesso não autorizado

### Auditoria
- Admin pode ver todas as transações para auditoria
- Partes podem ver suas próprias transações
- Público pode validar autenticidade sem ver dados sensíveis

## Template Considerations
O template `validar_fatura.html` deve ser atualizado para:

```jinja2
{% if acesso_completo %}
    <!-- Mostrar todos os dados -->
    <h2>Fatura {{ venda.fatura_ref }}</h2>
    <p>Comprador: {{ venda.comprador.nome }}</p>
    <p>Vendedor: {{ venda.vendedor.nome }}</p>
    <p>Valor: {{ venda.valor_total_pago }} Kz</p>
    <!-- ... mais detalhes ... -->
{% elif dados_publicos %}
    <!-- Mostrar apenas validação básica -->
    <h2>Validação de Fatura</h2>
    <p>✅ Fatura válida: {{ dados_publicos.fatura_ref }}</p>
    <p>Status: {{ dados_publicos.status }}</p>
    <p>Data: {{ dados_publicos.data_criacao }}</p>
    <p class="text-muted">Para ver detalhes completos, faça login como parte desta transação.</p>
{% else %}
    <!-- Fatura não encontrada -->
    <p>❌ {{ erro }}</p>
{% endif %}
```

## Status
✅ **CORRIGIDO** - Verificação de autorização implementada com dois níveis de acesso
🔒 **HIGH** - Esta correção protege dados pessoais e financeiros
🛡️ **PRIVACY** - Conforme GDPR/LGPD
📋 **COMPLIANCE** - Minimização de dados e controle de acesso
✅ **USABILITY** - Mantém funcionalidade de validação pública sem expor dados sensíveis
