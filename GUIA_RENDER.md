# 🔧 Configuração Render - Backend

## Passo 1: Criar Web Service

1. Aceder: https://dashboard.render.com
2. Clicar "New +" → "Web Service"
3. Conectar GitHub: `GervasioPedro/AgroKongo`
4. Configurar:

```yaml
Name: agrokongo-api
Region: Frankfurt
Branch: main
Root Directory: (deixar vazio)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn run:app --workers 2 --threads 4 --timeout 120
```

## Passo 2: Variáveis de Ambiente

Adicionar no Render (Environment):

```env
# Flask
FLASK_ENV=production

# Segurança (GERAR NOVA!)
SECRET_KEY=<executar: python -c "import secrets; print(secrets.token_hex(32))">

# Base de Dados (copiar do Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# CORS (atualizar depois com URL real do Netlify)
CORS_ORIGINS=https://agrokongo.netlify.app,https://www.agrokongo.ao

# Redis (criar depois)
REDIS_URL=redis://red-xxx:6379
```

## Passo 3: Criar Redis

1. No Render: "New +" → "Redis"
2. Name: agrokongo-redis
3. Region: Frankfurt
4. Copiar "Internal Redis URL"
5. Adicionar como REDIS_URL no Web Service

## Passo 4: Deploy

1. Clicar "Create Web Service"
2. Aguardar 5-7 minutos
3. Verificar logs (deve aparecer "Booting worker")

## Passo 5: Executar Migrações

No Render Dashboard → Shell (ou localmente):

```bash
# Conectar à base de dados
export DATABASE_URL="postgresql://postgres:..."

# Executar migrações
flask db upgrade

# Popular dados iniciais
python seed.py
```

## Passo 6: Testar

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

## ✅ Backend Pronto!

URL: https://agrokongo-api.onrender.com

Copiar esta URL para usar no Frontend (Netlify).
