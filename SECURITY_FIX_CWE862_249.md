# Correção CWE-862: Missing Authorization em main.py (Linhas 249-254)

## Status: ✅ CORRIGIDO

**Localização**: `app/routes/main.py` - Linhas 249-254  
**Função**: `perfil_produtor()`  
**Data da Correção**: Atual  

## Problema Identificado

A função `perfil_produtor()` era uma rota pública sem verificação de autorização, permitindo visualização de perfis de qualquer usuário, incluindo:
- Compradores (que não deveriam ter perfil público)
- Administradores (que não deveriam ter perfil público)
- Produtores não validados (contas pendentes de aprovação)

### Código ANTES (Vulnerável)

```python
@main_bp.route('/produtor/<int:id>')
def perfil_produtor(id):
    produtor = Usuario.query.get_or_404(id)
    avaliacoes = Avaliacao.query.filter_by(produtor_id=id).order_by(Avaliacao.data_criacao.desc()).all()

    # Cálculo da média usando SQLAlchemy func
    media = db.session.query(func.avg(Avaliacao.estrelas)).filter(Avaliacao.produtor_id == id).scalar() or 0

    return render_template('main/perfil_produtor.html',
                           produtor=produtor,
                           avaliacoes=avaliacoes,
                           media=round(media, 1))
```

### Problemas

1. **Sem Verificação de Tipo**: Qualquer usuário (comprador, admin) poderia ter perfil público
2. **Sem Verificação de Validação**: Produtores não validados tinham perfil visível
3. **Exposição de Dados**: Informações de usuários não-produtores poderiam ser expostas
4. **Enumeração de Usuários**: Atacante poderia iterar IDs para descobrir todos os usuários

## Correção Aplicada

### Código DEPOIS (Corrigido)

```python
@main_bp.route('/produtor/<int:id>')
def perfil_produtor(id):
    produtor = Usuario.query.get_or_404(id)
    
    # Verificação de autorização: apenas produtores validados têm perfil público
    if produtor.tipo != 'produtor':
        abort(404)  # Retorna 404 para não revelar existência de outros tipos de usuário
    
    if not produtor.conta_validada:
        abort(404)  # Perfil não visível se conta não validada
    
    avaliacoes = Avaliacao.query.filter_by(produtor_id=id).order_by(Avaliacao.data_criacao.desc()).all()

    # Cálculo da média usando SQLAlchemy func
    media = db.session.query(func.avg(Avaliacao.estrelas)).filter(Avaliacao.produtor_id == id).scalar() or 0

    return render_template('main/perfil_produtor.html',
                           produtor=produtor,
                           avaliacoes=avaliacoes,
                           media=round(media, 1))
```

### Melhorias

1. ✅ **Verificação de Tipo**: Apenas usuários do tipo 'produtor' têm perfil público
2. ✅ **Verificação de Validação**: Apenas produtores com `conta_validada=True`
3. ✅ **Retorno 404**: Usa 404 em vez de 403 para não revelar existência de usuários
4. ✅ **Proteção de Dados**: Informações de não-produtores não são expostas

## Análise de Segurança

### ✅ Proteções Implementadas

#### 1. Verificação de Tipo de Usuário
```python
if produtor.tipo != 'produtor':
    abort(404)
```
**Proteção**: 
- Apenas produtores têm perfil público
- Compradores e admins não são expostos
- Retorna 404 para não revelar tipos de usuário

#### 2. Verificação de Validação de Conta
```python
if not produtor.conta_validada:
    abort(404)
```
**Proteção**: 
- Apenas produtores validados pela administração
- Contas pendentes não são visíveis publicamente
- Mantém qualidade do marketplace

#### 3. Busca Segura
```python
produtor = Usuario.query.get_or_404(id)
```
**Proteção**: Retorna 404 se usuário não existir

## Matriz de Autorização

| Tipo de Usuário | Conta Validada | Perfil Público Visível |
|-----------------|----------------|------------------------|
| **Produtor** | ✅ Sim | ✅ Visível |
| **Produtor** | ❌ Não | ❌ HTTP 404 |
| **Comprador** | ✅ Sim | ❌ HTTP 404 |
| **Comprador** | ❌ Não | ❌ HTTP 404 |
| **Admin** | ✅ Sim | ❌ HTTP 404 |
| **Inexistente** | N/A | ❌ HTTP 404 |

## Cenários de Ataque Bloqueados

### 1. Visualização de Perfil de Comprador
```python
# Usuário ID 5 é um comprador
GET /produtor/5
```
**Resultado**:
- Busca usuário: OK
- Verifica: `produtor.tipo (comprador) != 'produtor'`
- **HTTP 404 Not Found**

### 2. Visualização de Perfil de Admin
```python
# Usuário ID 1 é admin
GET /produtor/1
```
**Resultado**:
- Busca usuário: OK
- Verifica: `produtor.tipo (admin) != 'produtor'`
- **HTTP 404 Not Found**

### 3. Visualização de Produtor Não Validado
```python
# Usuário ID 10 é produtor mas conta_validada=False
GET /produtor/10
```
**Resultado**:
- Busca usuário: OK
- Verifica tipo: OK (é produtor)
- Verifica: `not produtor.conta_validada`
- **HTTP 404 Not Found**

### 4. Enumeração de Usuários
```python
# Atacante tenta descobrir todos os usuários
for user_id in range(1, 1000):
    GET /produtor/{user_id}
```
**Resultado**:
- Apenas produtores validados retornam 200
- Todos os outros retornam 404
- **Enumeração limitada apenas a produtores públicos**

### 5. Visualização de Produtor Validado (Legítimo)
```python
# Usuário ID 15 é produtor validado
GET /produtor/15
```
**Resultado**:
- Busca usuário: OK
- Verifica tipo: OK (é produtor)
- Verifica validação: OK (conta_validada=True)
- **HTTP 200 OK - Perfil exibido**

## Comparação: Antes vs Depois

### ❌ ANTES (Vulnerável)

```python
@main_bp.route('/produtor/<int:id>')
def perfil_produtor(id):
    produtor = Usuario.query.get_or_404(id)
    # SEM VERIFICAÇÃO DE AUTORIZAÇÃO
    avaliacoes = Avaliacao.query.filter_by(produtor_id=id).order_by(Avaliacao.data_criacao.desc()).all()
    media = db.session.query(func.avg(Avaliacao.estrelas)).filter(Avaliacao.produtor_id == id).scalar() or 0
    return render_template('main/perfil_produtor.html', produtor=produtor, avaliacoes=avaliacoes, media=round(media, 1))
```

**Problemas**:
- ❌ Qualquer usuário tem perfil público
- ❌ Compradores expostos
- ❌ Admins expostos
- ❌ Produtores não validados expostos
- ❌ Possível enumeração completa de usuários

### ✅ DEPOIS (Corrigido)

```python
@main_bp.route('/produtor/<int:id>')
def perfil_produtor(id):
    produtor = Usuario.query.get_or_404(id)
    
    # VERIFICAÇÃO DE AUTORIZAÇÃO
    if produtor.tipo != 'produtor':
        abort(404)
    
    if not produtor.conta_validada:
        abort(404)
    
    avaliacoes = Avaliacao.query.filter_by(produtor_id=id).order_by(Avaliacao.data_criacao.desc()).all()
    media = db.session.query(func.avg(Avaliacao.estrelas)).filter(Avaliacao.produtor_id == id).scalar() or 0
    return render_template('main/perfil_produtor.html', produtor=produtor, avaliacoes=avaliacoes, media=round(media, 1))
```

**Proteções**:
- ✅ Apenas produtores têm perfil público
- ✅ Apenas produtores validados
- ✅ Compradores protegidos
- ✅ Admins protegidos
- ✅ Enumeração limitada

## Alinhamento com Outras Funções

Esta correção alinha `perfil_produtor()` com a lógica já implementada em `index()`:

### Função `index()` (Linha ~42)
```python
safras_recentes = Safra.query.join(Usuario, Safra.produtor_id == Usuario.id) \
    .filter(Safra.status == 'disponivel', Usuario.conta_validada == True) \
    .order_by(Safra.id.desc()).limit(4).all()
```
**Lógica**: Apenas safras de produtores validados são exibidas

### Função `perfil_produtor()` (Agora Corrigida)
```python
if produtor.tipo != 'produtor':
    abort(404)

if not produtor.conta_validada:
    abort(404)
```
**Lógica**: Apenas perfis de produtores validados são visíveis

**Consistência**: ✅ Ambas as funções seguem a mesma regra de negócio

## Impacto da Correção

### Segurança
✅ Previne exposição de dados de não-produtores  
✅ Protege informações de compradores e admins  
✅ Limita enumeração de usuários  
✅ Mantém qualidade do marketplace (apenas validados)  
✅ Retorna 404 para não revelar estrutura de usuários  

### Experiência do Usuário
✅ Marketplace mostra apenas produtores confiáveis  
✅ Usuários veem apenas perfis de produtores validados  
✅ Consistência com listagem de safras  
✅ Mensagem de erro apropriada (404)  

### Regras de Negócio
✅ Apenas produtores validados têm presença pública  
✅ Processo de KYC obrigatório antes de visibilidade  
✅ Administração controla quem aparece no marketplace  

## Testes de Validação

### Teste 1: Produtor Validado ✅
```python
# Usuário ID 10: tipo='produtor', conta_validada=True
GET /produtor/10
# Esperado: 200 OK - Perfil exibido
```

### Teste 2: Produtor Não Validado ❌
```python
# Usuário ID 11: tipo='produtor', conta_validada=False
GET /produtor/11
# Esperado: 404 Not Found
```

### Teste 3: Comprador ❌
```python
# Usuário ID 5: tipo='comprador', conta_validada=True
GET /produtor/5
# Esperado: 404 Not Found
```

### Teste 4: Admin ❌
```python
# Usuário ID 1: tipo='admin', conta_validada=True
GET /produtor/1
# Esperado: 404 Not Found
```

### Teste 5: Usuário Inexistente ❌
```python
GET /produtor/99999
# Esperado: 404 Not Found
```

## Análise de Código Seguro

### ✅ Boas Práticas Implementadas

1. **Whitelist Approach**: Apenas tipo 'produtor' permitido
2. **Validation Required**: Conta deve estar validada
3. **Fail Secure**: Nega acesso por padrão (404)
4. **Information Hiding**: Usa 404 em vez de 403
5. **Business Logic**: Alinhado com regras de negócio

### ✅ Proteções Contra OWASP Top 10

| Vulnerabilidade | Proteção | Status |
|-----------------|----------|--------|
| A01:2021 - Broken Access Control | Verificação de tipo e validação | ✅ |
| A05:2021 - Security Misconfiguration | Configuração segura | ✅ |

## Fluxo de Segurança

```
1. Requisição: GET /produtor/123
   ↓
2. Busca: Usuario.query.get_or_404(123)
   ↓ (Se não existe → HTTP 404)
3. Verificação Tipo: produtor.tipo == 'produtor'?
   ↓ NÃO → HTTP 404
   ↓ SIM → Continua
4. Verificação Validação: produtor.conta_validada?
   ↓ NÃO → HTTP 404
   ↓ SIM → Continua
5. Busca Avaliações: Query de avaliações
   ↓
6. Cálculo Média: Média de estrelas
   ↓
7. Resposta: Renderiza perfil público
```

## Recomendações Adicionais (Opcionais)

### 1. Cache de Perfis Públicos
```python
from flask_caching import Cache

@cache.cached(timeout=300, key_prefix='perfil_produtor')
def perfil_produtor(id):
    # ...
```

### 2. Rate Limiting
```python
from flask_limiter import Limiter

@limiter.limit("30 per minute")
def perfil_produtor(id):
    # ...
```

### 3. Logging de Acessos
```python
current_app.logger.info(f"Perfil do produtor {id} acessado")
```

## Conclusão

### ✅ VULNERABILIDADE CORRIGIDA

A função `perfil_produtor()` agora possui:

1. ✅ **Verificação de Tipo** - Apenas produtores
2. ✅ **Verificação de Validação** - Apenas contas validadas
3. ✅ **Busca Segura** - `get_or_404()`
4. ✅ **Resposta Apropriada** - HTTP 404 para não revelar estrutura
5. ✅ **Alinhamento** - Consistente com outras funções

### 🎯 Nível de Segurança: ALTO

- **Whitelist Approach**: Apenas produtores validados
- **Information Hiding**: Usa 404 para não revelar tipos
- **Business Logic**: Alinhado com regras de negócio
- **Fail Secure**: Nega acesso por padrão

### ✅ CORREÇÃO COMPLETA

A implementação agora protege adequadamente os perfis de usuários e mantém a qualidade do marketplace.

## Documentação Relacionada

- **SECURITY_FIX_CWE862_MAIN.md** - Outras correções de autorização
- **SECURITY_FIX_CWE862_350.md** - Correção de baixar_fatura()
- Este documento - Correção de perfil_produtor()

## Referências
- CWE-862: https://cwe.mitre.org/data/definitions/862.html
- OWASP Authorization: https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/
- OWASP Top 10 2021: https://owasp.org/Top10/
- Information Disclosure: https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings_in_url
