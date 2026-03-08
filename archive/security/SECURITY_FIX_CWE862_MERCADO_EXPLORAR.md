# Correção CWE-862: Missing Authorization em mercado.py (explorar)

## Vulnerabilidade Identificada
**Ficheiro:** `app/routes/mercado.py`  
**Linhas:** 16-40  
**Severidade:** MÉDIA  
**CWE:** CWE-862 (Missing Authorization)

## Descrição da Vulnerabilidade

### Função `explorar()` (linha 16)
- **Problema:** Vitrine pública exibia safras de produtores não validados
- **Risco:** Utilizadores não aprovados poderiam ter produtos visíveis no mercado
- **Impacto:** Quebra do modelo de negócio que exige validação administrativa antes de vender

## Correção Implementada

### Filtro de Validação na Query Principal
```python
query = Safra.query.options(
    joinedload(Safra.produto),
    joinedload(Safra.produtor).joinedload(Usuario.provincia)
).join(Usuario).filter(
    Safra.status == 'disponivel',
    Safra.quantidade_disponivel > 0,
    Usuario.conta_validada == True  # ← NOVO FILTRO
)
```

### Otimização do JOIN
**Antes:**
```python
if prov_id:
    query = query.join(Usuario).filter(Usuario.provincia_id == prov_id)
```

**Depois:**
```python
# JOIN já feito na query base
if prov_id:
    query = query.filter(Usuario.provincia_id == prov_id)
```

## Camadas de Proteção

1. ✅ JOIN com tabela Usuario na query base
2. ✅ Filtro `Usuario.conta_validada == True` aplicado a todas as safras
3. ✅ Filtro aplicado antes de qualquer outro filtro opcional (província, categoria)
4. ✅ Eager loading mantido para performance (evita N+1 queries)

## Impacto da Correção

### Segurança
- ✅ Apenas produtores validados aparecem na vitrine pública
- ✅ Consistência com outras rotas (`detalhes_safra`, `perfil_produtor`)
- ✅ Protege integridade do processo de validação administrativa

### Performance
- ✅ JOIN único na query base (não duplicado em filtros condicionais)
- ✅ Eager loading mantido para evitar N+1 queries
- ✅ Filtro aplicado ao nível da base de dados (não em Python)

### Modelo de Negócio
- ✅ Garante que apenas produtores aprovados vendem no AgroKongo
- ✅ Protege reputação da plataforma (apenas vendedores verificados)
- ✅ Mantém confiança do sistema de Escrow

## Testes Recomendados

1. **Produtor Validado:** Safras aparecem na vitrine ✅
2. **Produtor Não Validado:** Safras NÃO aparecem na vitrine ✅
3. **Filtro por Província:** Apenas produtores validados daquela província ✅
4. **Filtro por Categoria:** Apenas produtores validados daquela categoria ✅
5. **Performance:** Verificar que não há N+1 queries (usar Flask-DebugToolbar) ✅

## Status
✅ **CORRIGIDO** - Vitrine pública exibe apenas safras de produtores validados
