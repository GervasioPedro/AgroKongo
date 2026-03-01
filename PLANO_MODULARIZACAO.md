# 🏗️ PLANO DE MODULARIZAÇÃO - AGROKONGO

## 🎯 OBJETIVO
Melhorar a estrutura do código para facilitar manutenção e onboarding de novos programadores.

---

## 🔴 PROBLEMAS IDENTIFICADOS

### 1. Modelos Fragmentados
```
❌ models.py (principal)
❌ models_atualizado.py (duplicação?)
❌ models_carteiras.py
❌ models_disputa.py
```
**Problema:** Confusão sobre qual usar, possível código duplicado.

### 2. Decorators Duplicados
```
❌ decorators.py
❌ decorators_atualizado.py
```
**Problema:** Qual é a versão correta?

### 3. Rotas Duplicadas
```
❌ comprador.py
❌ comprador_v2.py
```
**Problema:** Duas versões do mesmo módulo.

### 4. Tasks Espalhadas
```
❌ app/tasks.py (raiz)
❌ app/tasks/ (pasta com múltiplos arquivos)
❌ app/services/tasks.py
```
**Problema:** Lógica de background jobs em 3 lugares diferentes.

### 5. Services Misturados
```
❌ app/services/reports.py
❌ app/routes/reports.py
```
**Problema:** Lógica de relatórios duplicada.

---

## ✅ ESTRUTURA PROPOSTA

```
app/
├── models/                    # 📦 MODELOS (Consolidados)
│   ├── __init__.py           # Exporta todos os modelos
│   ├── base.py               # Helpers e mixins comuns
│   ├── usuario.py            # Usuario, Provincia, Municipio
│   ├── produto.py            # Produto, Safra
│   ├── transacao.py          # Transacao, HistoricoStatus
│   ├── financeiro.py         # MovimentacaoFinanceira, Carteira
│   ├── notificacao.py        # Notificacao, AlertaPreferencia
│   ├── disputa.py            # Disputa
│   └── auditoria.py          # LogAuditoria, ConfiguracaoSistema
│
├── services/                  # 🔧 LÓGICA DE NEGÓCIO
│   ├── __init__.py
│   ├── escrow_service.py     # ✅ Já existe
│   ├── usuario_service.py    # Cadastro, validação, KYC
│   ├── transacao_service.py  # Criar, atualizar transações
│   ├── notificacao_service.py # ✅ Já existe
│   ├── financeiro_service.py # Cálculos, movimentações
│   ├── safra_service.py      # CRUD de safras
│   ├── disputa_service.py    # Gestão de disputas
│   └── relatorio_service.py  # Geração de relatórios
│
├── repositories/              # 🗄️ ACESSO A DADOS (Novo)
│   ├── __init__.py
│   ├── base_repository.py    # Classe base com CRUD genérico
│   ├── usuario_repository.py
│   ├── transacao_repository.py
│   └── safra_repository.py
│
├── routes/                    # 🌐 ENDPOINTS (Limpos)
│   ├── __init__.py
│   ├── auth.py               # Login, registo, logout
│   ├── admin.py              # Dashboard admin
│   ├── produtor.py           # Dashboard produtor
│   ├── comprador.py          # Dashboard comprador (consolidado)
│   ├── mercado.py            # Marketplace público
│   ├── disputas.py           # Gestão de disputas
│   ├── api/                  # APIs REST separadas
│   │   ├── __init__.py
│   │   ├── auth_api.py
│   │   ├── transacoes_api.py
│   │   └── wallet_api.py
│   └── handlers.py           # Error handlers
│
├── tasks/                     # ⏰ BACKGROUND JOBS (Consolidado)
│   ├── __init__.py
│   ├── celery_config.py      # Configuração do Celery
│   ├── faturas.py
│   ├── notificacoes.py
│   ├── pagamentos.py
│   ├── monitoramento.py      # Disputas + transações estagnadas
│   └── limpeza.py
│
├── utils/                     # 🛠️ UTILITÁRIOS
│   ├── __init__.py
│   ├── decorators.py         # Consolidado (sem duplicação)
│   ├── helpers.py            # Funções auxiliares
│   ├── validators.py         # Validações customizadas
│   └── constants.py          # Constantes do sistema
│
├── schemas/                   # 📋 VALIDAÇÃO (Novo)
│   ├── __init__.py
│   ├── usuario_schema.py     # Pydantic/Marshmallow schemas
│   ├── transacao_schema.py
│   └── safra_schema.py
│
├── middleware/                # 🔐 MIDDLEWARE (Novo)
│   ├── __init__.py
│   ├── auth_middleware.py
│   └── logging_middleware.py
│
├── __init__.py               # Factory
├── extensions.py             # Flask extensions
└── config.py                 # Movido para raiz (melhor prática)
```

---

## 📋 PLANO DE EXECUÇÃO

### FASE 1: Consolidar Modelos (2-3 horas)
1. ✅ Criar pasta `app/models/`
2. ✅ Dividir `models.py` em módulos específicos
3. ✅ Migrar `models_carteiras.py` → `models/financeiro.py`
4. ✅ Migrar `models_disputa.py` → `models/disputa.py`
5. ✅ Deletar `models_atualizado.py` (se for duplicado)
6. ✅ Atualizar imports em todo o projeto

### FASE 2: Expandir Services (3-4 horas)
1. ✅ Criar serviços faltantes
2. ✅ Mover lógica das rotas para services
3. ✅ Consolidar `services/reports.py` e `routes/reports.py`

### FASE 3: Criar Repositories (2 horas)
1. ✅ Criar camada de repositórios
2. ✅ Abstrair queries complexas
3. ✅ Facilitar testes unitários

### FASE 4: Limpar Routes (2 horas)
1. ✅ Consolidar `comprador.py` e `comprador_v2.py`
2. ✅ Mover lógica para services
3. ✅ Criar pasta `routes/api/` para endpoints REST

### FASE 5: Consolidar Tasks (1 hora)
1. ✅ Deletar `app/tasks.py` (raiz)
2. ✅ Consolidar em `app/tasks/`
3. ✅ Remover `services/tasks.py`

### FASE 6: Limpar Utils (1 hora)
1. ✅ Consolidar decorators
2. ✅ Deletar `decorators_atualizado.py`
3. ✅ Criar `validators.py` e `constants.py`

---

## 🎯 BENEFÍCIOS

### Para Novos Programadores
- ✅ **Estrutura clara** - Sabe onde encontrar cada coisa
- ✅ **Sem duplicação** - Não há confusão sobre qual arquivo usar
- ✅ **Separação de concerns** - Cada camada tem responsabilidade única

### Para Manutenção
- ✅ **Testes mais fáceis** - Services e repositories isolados
- ✅ **Menos bugs** - Lógica centralizada
- ✅ **Refatoração segura** - Mudanças localizadas

### Para Escalabilidade
- ✅ **Fácil adicionar features** - Estrutura extensível
- ✅ **Reutilização de código** - Services compartilhados
- ✅ **Performance** - Repositories otimizados

---

## 📊 COMPARAÇÃO

### ANTES (Atual)
```python
# Rota com lógica de negócio misturada
@admin_bp.route('/validar-pagamento/<int:id>', methods=['POST'])
def validar_pagamento(id):
    venda = Transacao.query.with_for_update().get_or_404(id)
    if venda.status != TransactionStatus.ANALISE:
        flash('Erro', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    venda.status = TransactionStatus.ESCROW
    db.session.add(LogAuditoria(...))
    db.session.add(Notificacao(...))
    db.session.commit()
    # ... 30+ linhas de lógica
```

### DEPOIS (Modularizado)
```python
# Rota limpa
@admin_bp.route('/validar-pagamento/<int:id>', methods=['POST'])
@admin_required
def validar_pagamento(id):
    sucesso, msg = EscrowService.validar_pagamento(id, current_user.id)
    flash(msg, 'success' if sucesso else 'danger')
    return redirect(url_for('admin.dashboard'))

# Lógica no service (testável, reutilizável)
class EscrowService:
    @staticmethod
    def validar_pagamento(transacao_id, admin_id):
        transacao = TransacaoRepository.get_with_lock(transacao_id)
        # ... lógica isolada
        return True, "Sucesso"
```

---

## ⚠️ RISCOS E MITIGAÇÃO

### Risco 1: Quebrar código existente
**Mitigação:** 
- Fazer em branches separadas
- Testes automatizados antes e depois
- Deploy gradual

### Risco 2: Tempo de desenvolvimento
**Mitigação:**
- Fazer por fases
- Priorizar módulos críticos
- Pode ser feito em paralelo com features

### Risco 3: Curva de aprendizado
**Mitigação:**
- Documentar cada camada
- Criar guia de contribuição
- Code review rigoroso

---

## 📝 CHECKLIST DE IMPLEMENTAÇÃO

### Preparação
- [ ] Criar branch `refactor/modularizacao`
- [ ] Fazer backup da base de dados
- [ ] Garantir cobertura de testes > 70%

### Fase 1: Modelos
- [ ] Criar `app/models/__init__.py`
- [ ] Dividir modelos por domínio
- [ ] Atualizar imports
- [ ] Rodar testes

### Fase 2: Services
- [ ] Criar services faltantes
- [ ] Mover lógica das rotas
- [ ] Criar testes unitários

### Fase 3: Repositories
- [ ] Criar base repository
- [ ] Implementar repositories específicos
- [ ] Atualizar services

### Fase 4: Routes
- [ ] Consolidar rotas duplicadas
- [ ] Limpar lógica de negócio
- [ ] Criar pasta API

### Fase 5: Tasks
- [ ] Consolidar tasks
- [ ] Remover duplicações
- [ ] Testar jobs assíncronos

### Fase 6: Utils
- [ ] Consolidar decorators
- [ ] Criar validators
- [ ] Criar constants

### Finalização
- [ ] Atualizar documentação
- [ ] Code review completo
- [ ] Merge para main
- [ ] Deploy em staging
- [ ] Monitorar por 48h
- [ ] Deploy em produção

---

## 🚀 PRÓXIMO PASSO

Queres que eu comece a implementar? Posso fazer:

1. **FASE 1 COMPLETA** - Consolidar todos os modelos (mais impactante)
2. **CRIAR APENAS ESTRUTURA** - Pastas e arquivos vazios (menos risco)
3. **EXEMPLO COMPLETO** - Um módulo completo (Usuario) como referência

Qual preferes? 🤔
