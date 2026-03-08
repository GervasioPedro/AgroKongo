# 🔧 Guia Completo de Deploy no Render - Backend AgroKongo

> **Última atualização:** Março 2026  
> **Versão:** 2.0  
> **Complexidade:** Intermediária

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Arquitetura de Deploy](#arquitetura-de-deploy)
4. [Opção A: Deploy via Blueprint (Recomendado)](#opção-a-deploy-via-blueprint-recomendado)
5. [Opção B: Deploy Manual](#opção-b-deploy-manual)
6. [Configuração de Variáveis de Ambiente](#configuração-de-variáveis-de-ambiente)
7. [Migrações e Seeds](#migrações-e-seeds)
8. [Verificação Pós-Deploy](#verificação-pós-deploy)
9. [Configuração de CI/CD](#configuração-de-cicd)
10. [Monitoramento e Logs](#monitoramento-e-logs)
11. [Troubleshooting](#troubleshooting)
12. [Segurança](#segurança)
13. [Escalamento](#escalamento)

---

## Visão Geral

Este guia cobre o deploy completo do backend AgroKongo no [Render](https://render.com), incluindo:

| Componente | Descrição | Tipo de Serviço |
|------------|-----------|-----------------|
| **agrokongo-api** | API Flask com Gunicorn | Web Service |
| **agrokongo-worker** | Worker Celery para tarefas assíncronas | Worker |
| **agrokongo-beat** | Agendador Celery Beat | Worker |
| **agrokongo-redis** | Cache e message broker | Redis |
| **PostgreSQL** | Base de dados (Supabase recomendado) | Externo |

---

## Pré-requisitos

Antes de começar, certifique-se de ter:

### Contas e Acesso
- [ ] Conta no [Render](https://dashboard.render.com) (GitHub login recomendado)
- [ ] Repositório no GitHub com o código do projeto
- [ ] Conta no [Supabase](https://supabase.com) (para base de dados)
- [ ] Acesso de admin ao repositório `GervasioPedro/AgroKongo`

### Ferramentas Locais
```bash
# Verificar instalações
git --version
python --version  # 3.11+
curl --version
```

### Arquivos Necessários no Repositório
Verifique se existem na raiz do projeto:
- [ ] `requirements.txt` - Dependências Python
- [ ] `render.yaml` - Configuração Infrastructure-as-Code
- [ ] `run.py` - Entry point da aplicação
- [ ] `celery_worker.py` - Configuração Celery
- [ ] `Procfile` - Alternativa ao render.yaml

---

## Arquitetura de Deploy

```
┌─────────────────────────────────────────────────────────────┐
│                         RENDER                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  agrokongo-api  │  │agrokongo-worker │  │agrokongo-   │ │
│  │   (Web Service) │  │   (Worker)      │  │beat (Worker)│ │
│  │   Porta: 10000  │  │                 │  │             │ │
│  └────────┬────────┘  └────────┬────────┘  └──────┬──────┘ │
│           │                    │                   │       │
│           └────────────────────┼───────────────────┘       │
│                                │                           │
│                     ┌──────────▼──────────┐               │
│                     │  agrokongo-redis    │               │
│                     │   (Message Broker)  │               │
│                     └──────────┬──────────┘               │
└────────────────────────────────┼──────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      SUPABASE           │
                    │  PostgreSQL + Storage   │
                    └─────────────────────────┘
```

---

## Opção A: Deploy via Blueprint (Recomendado)

O Blueprint permite deploy automatizado via arquivo [`render.yaml`](render.yaml:1).

### Passo 1: Preparar o render.yaml

O arquivo já existe no repositório. Verifique se está atualizado:

```yaml
services:
  # Backend API
  - type: web
    name: agrokongo-api
    env: python
    region: frankfurt
    plan: free
    buildCommand: "pip install -r requirements.txt && flask db upgrade"
    startCommand: "gunicorn run:app --workers 2 --threads 4 --timeout 120"
    healthCheckPath: /health
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: agrokongo-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
        sync: true
      - key: REDIS_URL
        fromService:
          name: agrokongo-redis
          type: redis
          property: connectionString
      - key: CORS_ORIGINS
        value: https://agrokongo.netlify.app,https://www.agrokongo.ao

  # Celery Worker
  - type: worker
    name: agrokongo-worker
    env: python
    region: frankfurt
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "celery -A celery_worker.celery worker --loglevel=info --concurrency=2"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: agrokongo-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: agrokongo-redis
          type: redis
          property: connectionString

  # Celery Beat
  - type: worker
    name: agrokongo-beat
    env: python
    region: frankfurt
    plan: free
    buildCommand: "pip install -r requirements.txt"
    startCommand: "celery -A celery_worker.celery beat --loglevel=info"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: agrokongo-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: agrokongo-redis
          type: redis
          property: connectionString

databases:
  - name: agrokongo-db
    databaseName: agrokongo
    user: agrokongo
    region: frankfurt
    plan: free

  - name: agrokongo-redis
    type: redis
    region: frankfurt
    plan: free
    maxmemoryPolicy: allkeys-lru
```

### Passo 2: Criar Blueprint no Dashboard

1. Aceda: https://dashboard.render.com/blueprints
2. Clique **"New Blueprint Instance"**
3. Selecione o repositório `GervasioPedro/AgroKongo`
4. O Render deteta automaticamente o [`render.yaml`](render.yaml:1)

### Passo 3: Configurar Variáveis Sensíveis

⚠️ **IMPORTANTE**: Antes de clicar "Apply", adicione manualmente as variáveis sensíveis no dashboard:

```bash
# No Render Dashboard → agrokongo-api → Environment

# Base de Dados (Substituir pelo seu Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# Segurança (Gerar nova chave)
SECRET_KEY=sua_chave_secreta_aqui_minimo_64_caracteres_hex

# Redis (Será preenchido automaticamente após criar o serviço)
REDIS_URL=redis://red-xxx:6379

# Supabase Storage
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE=eyJ...
SUPABASE_PUBLIC_URL=https://seu-projeto.supabase.co/storage/v1
SUPABASE_BUCKET=agrokongo-uploads

# Email (Opcional - para notificações)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app

# CORS (Atualizar com URL real do Netlify)
CORS_ORIGINS=https://agrokongo.netlify.app,https://www.agrokongo.ao,http://localhost:3000
```

### Passo 4: Aplicar Blueprint

1. Revise todos os serviços listados
2. Clique **"Apply"** ou **"Create"**
3. Aguarde 5-10 minutos para o deploy inicial

---

## Opção B: Deploy Manual

Use esta opção se precisar de mais controlo ou se o Blueprint falhar.

### Passo 1: Criar Redis

1. No Dashboard: **"New +"** → **"Redis"**
2. Configure:
   - **Name:** `agrokongo-redis`
   - **Region:** Frankfurt (ou a mesma do web service)
   - **Plan:** Free
3. Guarde o **Internal Redis URL** (será algo como `redis://red-xxx:6379`)

### Passo 2: Criar Web Service (API)

1. **"New +"** → **"Web Service"**
2. Conectar GitHub: `GervasioPedro/AgroKongo`
3. Configure:

| Campo | Valor |
|-------|-------|
| **Name** | `agrokongo-api` |
| **Region** | Frankfurt |
| **Branch** | `main` |
| **Root Directory** | (deixar vazio) |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn run:app --workers 2 --threads 4 --timeout 120` |

4. **Environment Variables**: Adicione todas as variáveis da seção anterior

### Passo 3: Criar Workers

**Worker Celery:**
1. **"New +"** → **"Worker"**
2. **Name:** `agrokongo-worker`
3. **Start Command:** `celery -A celery_worker.celery worker --loglevel=info --concurrency=2`
4. Adicione as mesmas variáveis de ambiente

**Beat Scheduler:**
1. **"New +"** → **"Worker"**
2. **Name:** `agrokongo-beat`
3. **Start Command:** `celery -A celery_worker.celery beat --loglevel=info`
4. Adicione as mesmas variáveis de ambiente

---

## Configuração de Variáveis de Ambiente

### Resumo das Variáveis

| Prioridade | Variável | Obrigatória | Descrição |
|------------|----------|-------------|-----------|
| 🔴 Alta | `DATABASE_URL` | Sim | Connection string PostgreSQL |
| 🔴 Alta | `SECRET_KEY` | Sim | Chave secreta Flask (64 chars) |
| 🔴 Alta | `REDIS_URL` | Sim | URL do Redis |
| 🔴 Alta | `FLASK_ENV` | Sim | `production` |
| 🟡 Média | `CORS_ORIGINS` | Sim | Domínios permitidos |
| 🟡 Média | `SUPABASE_URL` | Recomendada | URL do Supabase |
| 🟡 Média | `SUPABASE_SERVICE_ROLE` | Recomendada | Chave service_role |
| 🟢 Baixa | `MAIL_*` | Opcional | Config SMTP |

### Gerar SECRET_KEY

```bash
# Localmente, execute:
python -c "import secrets; print(secrets.token_hex(32))"

# Ou use o script incluído:
python gerar_secret_key.py
```

### Configurar CORS_ORIGINS

```bash
# Produção (Netlify)
CORS_ORIGINS=https://agrokongo.netlify.app,https://www.agrokongo.ao

# Desenvolvimento (incluir localhost)
CORS_ORIGINS=https://agrokongo.netlify.app,http://localhost:3000,http://localhost:5173

# Múltiplos domínios (separados por vírgula, sem espaços)
CORS_ORIGINS=https://app.agrokongo.ao,https://admin.agrokongo.ao,https://agrokongo.netlify.app
```

---

## Migrações e Seeds

### Executar Migrações

**Opção 1: Automático (no Build Command)**
```yaml
buildCommand: "pip install -r requirements.txt && flask db upgrade"
```

**Opção 2: Manual (via Shell do Render)**
```bash
# No Render Dashboard → agrokongo-api → Shell
cd /opt/render/project/src
export DATABASE_URL="postgresql://..."
flask db upgrade
```

### Popular Dados Iniciais

```bash
# No Shell do Render
cd /opt/render/project/src
python seed.py
```

### Verificar Estado da BD

```bash
# Listar tabelas
flask shell
>>> from app import db
>>> from sqlalchemy import inspect
>>> inspector = inspect(db.engine)
>>> print(inspector.get_table_names())
```

---

## Verificação Pós-Deploy

### Health Check

```bash
# Verificar se a API está online
curl https://agrokongo-api.onrender.com/health

# Resposta esperada:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-03-04T23:00:00Z",
  "version": "1.0.0"
}
```

### Testar Endpoints Principais

```bash
# 1. Testar CORS
curl -H "Origin: https://agrokongo.netlify.app" \
     -I https://agrokongo-api.onrender.com/health

# Verificar header: Access-Control-Allow-Origin

# 2. Testar API de autenticação
curl -X POST https://agrokongo-api.onrender.com/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"teste@exemplo.com","password":"teste123"}'

# 3. Verificar documentação Swagger (se configurada)
open https://agrokongo-api.onrender.com/docs
```

### Verificar Workers

```bash
# No Dashboard → agrokongo-worker → Logs
# Deve mostrar: "Connected to redis://..."

# Testar tarefa assíncrona (se houver endpoint)
curl -X POST https://agrokongo-api.onrender.com/api/test/task
```

---

## Configuração de CI/CD

### Auto-Deploy

Por padrão, o Render faz deploy automático a cada push na branch `main`.

Para desativar:
1. Dashboard → agrokongo-api → Settings
2. Desmarcar **"Auto-Deploy"**

### Deploy Manual

```bash
# Na página do serviço, clique "Manual Deploy" → "Deploy latest commit"
```

### Preview Environments (Pro/Team)

Para criar ambientes de preview para Pull Requests:
1. Dashboard → Blueprint Settings
2. Ativar **"Enable Pull Request Previews"**

---

## Monitoramento e Logs

### Aceder Logs

**Dashboard:**
1. Selecione o serviço
2. Clique em **"Logs"** (tab superior)

**CLI (opcional):**
```bash
# Instalar Render CLI
curl -fsSL https://raw.githubusercontent.com/render-oss/cli/main/bin/install.sh | bash

# Ver logs
render logs --service agrokongo-api
```

### Configurar Alertas

1. Dashboard → Settings → Alert Policies
2. Adicionar alertas para:
   - CPU > 80%
   - Memory > 85%
   - Disk > 90%
   - Service Down

### Métricas Importantes

| Métrica | Limite Aviso | Limite Crítico |
|---------|--------------|----------------|
| CPU Usage | > 70% | > 90% |
| Memory | > 75% | > 90% |
| Response Time | > 500ms | > 2000ms |
| Error Rate | > 1% | > 5% |

---

## Troubleshooting

### Problemas Comuns

#### 1. "ModuleNotFoundError" no Build

**Causa:** [`requirements.txt`](requirements.txt:1) não está na raiz ou dependência em falta.

**Solução:**
```bash
# Verificar estrutura
ls -la requirements.txt

# Verificar se o pacote está no requirements.txt
grep "nome_do_pacote" requirements.txt

# Reinstalar dependências
pip freeze > requirements.txt
```

#### 2. "DATABASE_URL not set"

**Causa:** Variável não definida ou `fromDatabase` falhou.

**Solução:**
```bash
# Verificar no Dashboard → Environment
# Adicionar manualmente se necessário:
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
```

#### 3. "SECRET_KEY not configured"

**Causa:** Variável em falta ou gerada incorretamente.

**Solução:**
```bash
# Gerar nova chave
python -c "import secrets; print(secrets.token_hex(32))"

# Adicionar no Dashboard (mínimo 64 caracteres hex)
```

#### 4. Erro de Migração "flask db upgrade"

**Causa:** Migrações desatualizadas ou BD inacessível.

**Solução:**
```bash
# No Shell do Render
cd /opt/render/project/src

# Verificar estado
flask db current
flask db history

# Reset (CUIDADO: apaga dados!)
flask db downgrade base
flask db upgrade
```

#### 5. Redis Connection Failed

**Causa:** Serviço Redis não iniciado ou URL incorreta.

**Solução:**
```bash
# Verificar se o serviço Redis está "Live"
# Verificar REDIS_URL no Environment
# Testar conexão:
redis-cli -u $REDIS_URL ping
```

#### 6. CORS Errors no Frontend

**Causa:** Domínio do frontend não está em `CORS_ORIGINS`.

**Solução:**
```bash
# Atualizar variável no Render
CORS_ORIGINS=https://agrokongo.netlify.app,https://novo-dominio.com

# Reiniciar serviço
```

#### 7. Worker Não Processa Tarefas

**Causa:** Worker não iniciado ou fila incorreta.

**Solução:**
```bash
# Verificar logs do worker
# Reiniciar worker manualmente
# Verificar se REDIS_URL está correta
```

#### 8. Timeout em Requests

**Causa:** Gunicorn timeout muito baixo.

**Solução:**
```yaml
# No render.yaml ou Dashboard, aumentar timeout:
startCommand: "gunicorn run:app --workers 2 --threads 4 --timeout 300"
```

### Logs de Debug

```bash
# Ativar debug temporariamente (não usar em produção!)
FLASK_ENV=development

# Ver logs detalhados do Gunicorn
gunicorn run:app --workers 2 --threads 4 --timeout 120 --log-level debug --access-logfile -
```

---

## Segurança

### Checklist de Segurança

- [ ] `SECRET_KEY` tem pelo menos 64 caracteres hex
- [ ] `FLASK_ENV=production` em todos os serviços
- [ ] `CORS_ORIGINS` não inclui `*`
- [ ] Variáveis sensíveis (`MAIL_PASSWORD`, `SUPABASE_SERVICE_ROLE`) têm `sync: false`
- [ ] HTTPS obrigatório (Render faz isto automaticamente)
- [ ] Headers de segurança configurados ([`config.py`](config.py:1))

### Headers de Segurança

O projeto usa [`flask-talisman`](requirements.txt:46) para headers de segurança:

```python
# config.py
TALISMAN_FORCE_HTTPS = True
TALISMAN_CONTENT_SECURITY_POLICY = {
    'default-src': "'self'",
    'script-src': "'self'",
    'style-src': ["'self'", "'unsafe-inline'"],
}
```

### Rotação de SECRET_KEY

```bash
# 1. Gerar nova chave
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Atualizar no Render Dashboard

# 3. Reiniciar todos os serviços (workers e api)

# Nota: Sessões ativas serão invalidadas
```

---

## Escalamento

### Upgrade de Plano

Para maior performance, upgrade do plano Free:

| Plano | CPU | RAM | Preço |
|-------|-----|-----|-------|
| Free | Compartilhado | 512 MB | $0 |
| Starter | 1 vCPU | 1 GB | $7/mês |
| Standard | 2 vCPU | 2 GB | $25/mês |
| Pro | 4 vCPU | 4 GB | $85/mês |

### Otimização de Workers Gunicorn

```bash
# Fórmula: (2 x $num_cores) + 1
# Para plano Starter (1 CPU):
gunicorn run:app --workers 3 --threads 2 --timeout 120

# Para plano Standard (2 CPUs):
gunicorn run:app --workers 5 --threads 4 --timeout 120
```

### Otimização de Concorrência Celery

```bash
# Ajustar conforme RAM disponível
# Free tier (512MB): concurrency=1
# Starter (1GB): concurrency=2
# Standard (2GB): concurrency=4

celery -A celery_worker.celery worker --loglevel=info --concurrency=2
```

---

## Comandos Úteis

```bash
# Restart de serviços
curl -X POST https://api.render.com/v1/services/{service_id}/restart \
  -H "Authorization: Bearer {api_key}"

# Ver status de todos os serviços
render services list

# Shell interativo no serviço
render ssh agrokongo-api

# Exportar logs
render logs --service agrokongo-api --tail 1000 > logs.txt
```

---

## Recursos Adicionais

- 📚 [Documentação Render](https://render.com/docs)
- 🐍 [Deploy Flask no Render](https://render.com/docs/deploy-flask)
- 🔄 [Render Blueprints](https://render.com/docs/blueprint-spec)
- 📊 [Celery no Render](https://render.com/docs/deploy-celery)
- 🔐 [Segurança no Render](https://render.com/docs/security)

---

## Suporte

Em caso de problemas:

1. Verifique os logs no Dashboard
2. Consulte a seção [Troubleshooting](#troubleshooting)
3. Verifique [`RENDER_ENVIRONMENT_CHECKLIST.md`](RENDER_ENVIRONMENT_CHECKLIST.md:1)
4. Abra um issue no GitHub com os logs de erro

---

**Nota:** Guarde sempre uma cópia local das suas variáveis de ambiente num ficheiro `.env` seguro (não commitado).

```bash
# Backup das variáveis
render env export agrokongo-api > .env.backup
