# ✅ Checklist Configuração Environment - Render

## 🔴 Problemas Comuns e Soluções

### 1. Erro: "DATABASE_URL não configurada"
**Causa**: O Render não consegue aceder à variável `DATABASE_URL`

**Solução**:
```yaml
# Se estiver a usar Supabase (recomendado), NÃO use fromDatabase
# Em vez disso, adicione manualmente no Dashboard do Render

# No render.yaml, remova ou comente:
# - key: DATABASE_URL
#   fromDatabase:
#     name: agrokongo-db
#     property: connectionString

# E adicione no Dashboard → Environment Variables:
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
```

---

### 2. Erro: "SECRET_KEY de produção não configurada"
**Causa**: A variável SECRET_KEY está vazia ou não definida

**Solução**:
```bash
# Gere uma nova chave localmente:
python -c "import secrets; print(secrets.token_hex(32))"

# Ou use o script do projeto:
python gerar_secret_key.py
```

Adicione no Render Dashboard:
```
SECRET_KEY=a_sua_chave_gerada_aqui_com_64_caracteres_hex
```

---

### 3. Erro: "No module named 'flask'" ou "ImportError"
**Causa**: O requirements.txt não está a ser instalado corretamente

**Solução**:
- Verifique se o `requirements.txt` está na raiz do projeto
- Verifique o Build Command no Render:
```
pip install -r requirements.txt
```

---

### 4. Erro de Migração: "flask db upgrade" falha
**Causa**: A base de dados ainda não existe ou as migrações estão desatualizadas

**Solução Manual (Shell do Render)**:
```bash
# No Render Dashboard → Shell
export DATABASE_URL="postgresql://postgres:..."
cd /opt/render/project/src
flask db upgrade
```

---

## 📋 Configuração Completa das Variáveis de Ambiente

### Variáveis OBRIGATÓRIAS (sem estas, não funciona):

| Variável | Valor | Onde Obter |
|----------|-------|------------|
| `DATABASE_URL` | `postgresql://postgres:[PASS]@db.xxx.supabase.co:5432/postgres` | Supabase → Project Settings → Database |
| `SECRET_KEY` | Chave de 64 caracteres hex | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_ENV` | `production` | Definir manualmente |
| `REDIS_URL` | `redis://red-xxx:6379` | Render → Redis service (criar primeiro) |

### Variáveis RECOMENDADAS:

| Variável | Valor | Notas |
|----------|-------|-------|
| `CORS_ORIGINS` | `https://agrokongo.netlify.app` | URL do frontend Netlify |
| `PYTHON_VERSION` | `3.11.0` | Versão Python |

### Variáveis OPCIONAIS (para funcionalidades extras):

| Variável | Valor | Funcionalidade |
|----------|-------|----------------|
| `SUPABASE_URL` | `https://xxx.supabase.co` | Storage de ficheiros |
| `SUPABASE_SERVICE_ROLE` | `eyJ...` | Chave service_role do Supabase |
| `SUPABASE_PUBLIC_URL` | `https://xxx.supabase.co/storage/v1` | URL pública do storage |
| `MAIL_SERVER` | `smtp.gmail.com` | Envio de emails |
| `MAIL_PORT` | `587` | Porta SMTP |
| `MAIL_USERNAME` | `email@gmail.com` | Email de envio |
| `MAIL_PASSWORD` | `senha_app` | Senha de app |
| `MAIL_USE_TLS` | `True` | Segurança SMTP |

---

## 🔧 Passo a Passo para Configurar

### Opção A: Usar Blueprint (render.yaml)

1. Vá para https://dashboard.render.com/blueprints
2. Clique "New Blueprint Instance"
3. Conecte o repositório GitHub
4. O Render vai detetar automaticamente o `render.yaml`
5. **IMPORTANTE**: Edite as variáveis antes de criar!

### Opção B: Criar Manualmente (Mais Controlo)

1. **Criar Redis primeiro**:
   - New + → Redis
   - Name: `agrokongo-redis`
   - Region: Frankfurt
   - Guardar o URL

2. **Criar Web Service**:
   - New + → Web Service
   - Conectar GitHub
   - Configurar:
     - Name: `agrokongo-api`
     - Environment: Python 3
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn run:app --workers 2 --threads 4 --timeout 120`

3. **Adicionar Environment Variables** (ver tabela acima)

---

## 🧪 Testar a Configuração

Depois do deploy, teste:

```bash
# Health check
curl https://agrokongo-api.onrender.com/health

# Deve retornar:
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

---

## 🚨 Troubleshooting Rápido

| Erro | Solução Rápida |
|------|----------------|
| `ModuleNotFoundError` | Verificar requirements.txt na raiz |
| `DATABASE_URL not set` | Adicionar variável manualmente no Dashboard |
| `SECRET_KEY not configured` | Gerar e adicionar SECRET_KEY |
| `Connection refused` | Verificar se a URL da base de dados está correta |
| `CORS error` | Atualizar CORS_ORIGINS com URL do frontend |
| `Redis connection failed` | Verificar se o serviço Redis está criado e URL correta |

---

## 📞 Precisa de Mais Ajuda?

Verifique os logs no Render Dashboard:
1. Vá para o serviço
2. Clique em "Logs"
3. Procure por mensagens de erro em vermelho

Copie e cole o erro específico para receber ajuda direcionada.
