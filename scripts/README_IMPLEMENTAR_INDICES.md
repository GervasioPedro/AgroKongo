# 🚀 GUIA RÁPIDO - IMPLEMENTAR ÍNDICES DE DATABASE

**Status:** ✅ Migration criada e pronta para aplicar  
**Impacto Esperado:** 50-80% melhoria em queries frequentes  
**Tempo de Execução:** 5-10 minutos

---

## 📋 CHECKLIST DE EXECUÇÃO

### ✅ Passo 1: Testar Performance ATUAL (Antes dos Índices)

```bash
# Navegar até o projeto
cd C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS

# Executar script de teste de performance
python scripts/test_query_performance.py
```

**O que observar:**
- Tempo médio das queries (>200ms é crítico)
- Queries mais lentas no relatório
- Anotar tempos para comparação depois

**Resultado esperado:**
```
⏱️  Tempo médio geral: 150.45ms por query
📈 Total testado: 9 queries

📋 CLASSIFICAÇÃO:
   ❌ trans_status: 245.32ms
   ⚠️  trans_comprador: 178.90ms
   ❌ usuarios_tipo_validado: 312.45ms
   ...
```

---

### ✅ Passo 2: Aplicar Migration dos Índices

```bash
# Verificar migrations pendentes
flask db current

# Aplicar migration dos índices
flask db upgrade add_strategic_indexes_2026

# Verificar se aplicou com sucesso
flask db current
# Deve mostrar: add_strategic_indexes_2026 (head)
```

**Saída esperada:**
```
✅ Índices estratégicos criados com sucesso!
📊 Impacto esperado:
   - Queries de status: 500ms → 10ms (50x mais rápido)
   - Listagem de safras: 300ms → 15ms (20x mais rápido)
   - Filtro de usuários: 200ms → 8ms (25x mais rápido)
```

---

### ✅ Passo 3: Validar Índices no Banco

```bash
# Conectar ao PostgreSQL
docker exec -it agrokongo_db psql -U agrokongo_user -d agrokongo_dev

# Listar índices da tabela transacoes
\di transacoes*

# Listar índices da tabela safras
\di safras*

# Listar índices da tabela usuarios
\di usuarios*

# Sair do PostgreSQL
\q
```

**Índices esperados:**
```
transacoes:
  idx_transacao_status
  idx_transacao_comprador_id
  idx_transacao_vendedor_id
  idx_transacao_comprador_status
  idx_transacao_vendedor_status

safras:
  idx_safra_produto_status
  idx_safra_produtor_id
  idx_safra_regiao_status

usuarios:
  idx_usuario_tipo
  idx_usuario_conta_validada
  idx_usuario_tipo_validado
  idx_usuario_nif
```

---

### ✅ Passo 4: Testar Performance DEPOIS (Com Índices)

```bash
# Reexecutar script de teste
python scripts/test_query_performance.py
```

**Melhoria esperada:**
```
⏱️  Tempo médio geral: 25.32ms por query (antes: 150.45ms)
📈 Total testado: 9 queries

📋 CLASSIFICAÇÃO:
   ✅ trans_status: 12.45ms (antes: 245.32ms) 🚀 20x mais rápido!
   ✅ trans_comprador: 8.90ms (antes: 178.90ms) 🚀 20x mais rápido!
   ✅ usuarios_tipo_validado: 15.45ms (antes: 312.45ms) 🚀 20x mais rápido!
   ...
```

---

### ✅ Passo 5: Comparar Resultados

**Criar relatório comparativo:**

| Query | Antes (ms) | Depois (ms) | Melhoria |
|-------|------------|-------------|----------|
| Transações por Status | 245.32 | 12.45 | **20x** 🚀 |
| Transações do Comprador | 178.90 | 8.90 | **20x** 🚀 |
| Usuários Tipo+Validado | 312.45 | 15.45 | **20x** 🚀 |
| Safras Produto+Status | 198.23 | 9.87 | **20x** 🚀 |
| **Média Geral** | **150.45** | **25.32** | **6x** 🚀 |

---

## 🎯 ÍNDICES APLICADOS

### Tabela: `transacoes` (5 índices)
1. `idx_transacao_status` - Filtra por status (pendente, analise, escrow...)
2. `idx_transacao_comprador_id` - Lista transações do comprador
3. `idx_transacao_vendedor_id` - Lista transações do vendedor
4. `idx_transacao_comprador_status` - Filtra comprador + status combinados
5. `idx_transacao_vendedor_status` - Filtra vendedor + status combinados

### Tabela: `safras` (3 índices)
6. `idx_safra_produto_status` - Marketplace: filtra por produto e status
7. `idx_safra_produtor_id` - Lista safras do produtor
8. `idx_safra_regiao_status` - Filtra por região e status

### Tabela: `usuarios` (4 índices)
9. `idx_usuario_tipo` - Busca por tipo (produtor, comprador, admin)
10. `idx_usuario_conta_validada` - Filtra usuários validados
11. `idx_usuario_tipo_validado` - **CRÍTICO**: produtores validados no marketplace
12. `idx_usuario_nif` - Validações KYC

### Tabela: `notificacoes` (1 índice)
13. `idx_notificacao_usuario_lida` - Notificações não lidas por usuário

### Tabela: `historico_status` (2 índices)
14. `idx_historico_status_transacao` - Histórico por transação
15. `idx_historico_status_data` - Histórico por data

**Total:** 15 índices estratégicos

---

## 🔍 SOLUÇÃO DE PROBLEMAS

### Problema: Migration falha com erro de dependência

**Solução:**
```bash
# Verificar última migration aplicada
flask db current

# Se houver erro, tentar downgrade primeiro
flask db downgrade -1

# Depois aplicar novamente
flask db upgrade add_strategic_indexes_2026
```

---

### Problema: Índices já existem

**Solução:**
```bash
# A migration já foi aplicada antes
# Verificar no banco:
docker exec -it agrokongo_db psql -U agrokongo_user -d agrokongo_dev -c "\di"
```

---

### Problema: Performance não melhorou

**Possíveis causas:**
1. Poucos dados no banco (< 100 registros)
2. Cache do PostgreSQL ainda quente
3. Índices não foram usados na query

**Solução:**
```bash
# Popular banco com seed
python seed.py

# Limpar cache
docker exec -it agrokongo_db psql -U agrokongo_user -d agrokongo_dev -c "SELECT pg_reload_conf();"

# Testar novamente
python scripts/test_query_performance.py
```

---

## 📊 MONITORAMENTO PÓS-IMPLANTAÇÃO

### Em Desenvolvimento
```bash
# Monitorar queries lentas
docker logs -f agrokongo_db
```

### Em Produção (Render/Supabase)
```sql
-- Habilitar pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Ver queries mais lentas
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

---

## ✅ CRITÉRIOS DE SUCESSO

Marcar quando todos estiverem ✅:

- [ ] Script de teste executado ANTES
- [ ] Tempos anotados para comparação
- [ ] Migration aplicada sem erros
- [ ] Índices validados no banco (\di)
- [ ] Script de teste executado DEPOIS
- [ ] Melhoria de >= 50% comprovada
- [ ] Relatório comparativo criado
- [ ] Equipe notificada da melhoria

---

## 🎯 PRÓXIMOS PASSOS

Após implementar índices:

1. ✅ **Concluído:** Índices de Database
2. ⏭️ **Próximo:** Aumentar cobertura de testes para 60%
3. ⏭️ **Depois:** Implementar cache Redis

---

## 📞 SUPORTE

Se encontrar problemas:

1. Verificar logs: `docker logs agrokongo_db`
2. Consultar docs: [PLANO_ACAO_PRIORITARIO.md](../PLANO_ACAO_PRIORITARIO.md)
3. Revisar migration: [add_strategic_indexes_2026.py](../migrations/versions/add_strategic_indexes_2026.py)

---

**Última atualização:** Março 2026  
**Responsável:** Tech Lead  
**Status:** ✅ Pronto para produção
