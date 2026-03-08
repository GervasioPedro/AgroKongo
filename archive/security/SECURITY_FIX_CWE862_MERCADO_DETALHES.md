# Correção CWE-862: Missing Authorization em mercado.py

## Vulnerabilidade Identificada
**Ficheiro:** `app/routes/mercado.py`  
**Linhas:** 59, 71  
**Severidade:** MÉDIA  
**CWE:** CWE-862 (Missing Authorization)

## Descrição da Vulnerabilidade

### 1. Função `detalhes_safra()` (linha 59)
- **Problema:** Rota pública expunha detalhes de safras de produtores não validados
- **Risco:** Utilizadores não validados poderiam ter produtos visíveis no mercado público
- **Impacto:** Quebra do modelo de negócio que exige validação antes de vender

### 2. Função `perfil_produtor()` (linha 71)
- **Problema:** Verificava apenas se era produtor, mas não se estava validado
- **Risco:** Perfis públicos de produtores não validados acessíveis
- **Impacto:** Exposição de informações de contas não aprovadas

## Correção Implementada

### 1. `detalhes_safra()` - Validação de Produtor
```python
safra = Safra.query.options(joinedload(Safra.produtor)).get_or_404(id)

if not safra.produtor.conta_validada:
    abort(404)
```
**Proteção:** Apenas safras de produtores validados são exibidas publicamente

### 2. `perfil_produtor()` - Verificação Dupla
```python
if produtor.tipo != 'produtor' or not produtor.conta_validada:
    abort(404)
```
**Proteção:** Perfis públicos apenas para produtores validados

## Camadas de Proteção

### `detalhes_safra()`
1. ✅ Eager loading do produtor para evitar N+1 queries
2. ✅ Verificação de `conta_validada` do produtor
3. ✅ Retorna 404 se produtor não validado (não expõe existência)

### `perfil_produtor()`
1. ✅ Verificação de tipo de conta (`tipo == 'produtor'`)
2. ✅ Verificação de validação (`conta_validada == True`)
3. ✅ Retorna 404 para ambos os casos (não distingue motivo)

## Impacto da Correção
- ✅ Apenas produtores validados têm safras visíveis no mercado
- ✅ Apenas produtores validados têm perfis públicos acessíveis
- ✅ Mantém consistência com regra de negócio do AgroKongo
- ✅ Protege integridade do sistema de validação administrativa

## Compliance
- **Modelo de Negócio:** Validação obrigatória antes de vender
- **Segurança:** Previne exposição de contas não aprovadas
- **UX:** Utilizadores públicos veem apenas conteúdo verificado

## Status
✅ **CORRIGIDO** - Autorização implementada em rotas públicas de mercado
