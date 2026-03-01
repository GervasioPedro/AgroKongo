# Correção CWE-862: Missing Authorization em mercado.py (média regional)

## Vulnerabilidade Identificada
**Ficheiro:** `app/routes/mercado.py`  
**Linhas:** 55-58 (dentro da função `detalhes_safra`)  
**Severidade:** BAIXA-MÉDIA  
**CWE:** CWE-862 (Missing Authorization)

## Descrição da Vulnerabilidade

### Cálculo de Média de Preço Regional
- **Problema:** Query calculava média de preços incluindo safras de produtores não validados
- **Risco:** Preços de referência manipulados por contas não aprovadas
- **Impacto:** Compradores recebem informação de mercado incorreta/manipulada

### Cenário de Exploração
1. Atacante cria conta de produtor (não validada)
2. Publica safras com preços artificialmente baixos/altos
3. Média regional é distorcida
4. Compradores tomam decisões baseadas em dados manipulados

## Correção Implementada

### Query com Filtro de Validação
**Antes:**
```python
media_regiao = db.session.query(func.avg(Safra.preco_por_unidade)).filter(
    Safra.produto_id == safra.produto_id,
    Safra.status == 'disponivel'
).scalar() or safra.preco_por_unidade
```

**Depois:**
```python
media_regiao = db.session.query(func.avg(Safra.preco_por_unidade)).join(Usuario).filter(
    Safra.produto_id == safra.produto_id,
    Safra.status == 'disponivel',
    Usuario.conta_validada == True
).scalar() or safra.preco_por_unidade
```

## Camadas de Proteção

1. ✅ JOIN com tabela Usuario
2. ✅ Filtro `Usuario.conta_validada == True`
3. ✅ Apenas safras disponíveis (status == 'disponivel')
4. ✅ Apenas mesmo produto (produto_id)
5. ✅ Fallback para preço da safra atual se não houver média

## Impacto da Correção

### Integridade de Dados
- ✅ Média de preços calculada apenas com produtores verificados
- ✅ Informação de mercado confiável para compradores
- ✅ Previne manipulação de preços de referência

### Consistência
- ✅ Alinhado com filtro da vitrine (`explorar`)
- ✅ Alinhado com validação de detalhes (`detalhes_safra`)
- ✅ Todas as queries públicas filtram por `conta_validada`

### Modelo de Negócio
- ✅ Apenas produtores aprovados influenciam preços de mercado
- ✅ Protege integridade do sistema de precificação
- ✅ Mantém confiança na plataforma AgroKongo

## Testes Recomendados

1. **Produtor Validado:** Preço incluído na média ✅
2. **Produtor Não Validado:** Preço NÃO incluído na média ✅
3. **Sem Safras Validadas:** Fallback para preço da safra atual ✅
4. **Múltiplos Produtos:** Média calculada apenas para produto específico ✅

## Status
✅ **CORRIGIDO** - Média de preços calculada apenas com produtores validados
