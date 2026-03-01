# 🚀 Deploy AgroKongo em Produção

## 📋 Arquitetura de Deploy

```
┌─────────────────┐         ┌──────────────────┐
│  Frontend       │         │   Backend        │
│  Next.js        │ ──────> │   Flask + API    │
│  (Netlify)      │  HTTPS  │   (Render/Railway)│
└─────────────────┘         └──────────────────┘
                                     │
                            ┌────────┴────────┐
                            │   PostgreSQL    │
                            │   (Supabase)    │
                            └─────────────────┘
```

## 🎯 Plataformas Recomendadas

### Frontend (Next.js)
- **Netlify** ✅ (Gratuito, CDN global)
- Alternativa: Vercel

### Backend (Flask)
- **Render** ✅ (Gratuito com limitações)
- **Railway** ✅ ($5/mês, melhor performance)
- Alternativa: Heroku, AWS

### Base de Dados
- **Supabase** ✅ (PostgreSQL gratuito, 500MB)
- Alternativa: Neon, ElephantSQL

### Storage de Ficheiros
- **Cloudinary** ✅ (Imagens gratuitas, 25GB)
- Alternativa: AWS S3, Supabase Storage

---

## 📦 PARTE 1: Preparar Frontend (Netlify)

### 1.1 Configurar variáveis de ambiente

Criar `frontend/.env.production`:
```env
NEXT_PUBLIC_API_URL=https://agrokongo-api.onrender.com
NEXT_PUBLIC_APP_URL=https://agrokongo.netlify.app
```

### 1.2 Criar ficheiro de configuração Netlify

Criar `frontend/netlify.toml`:
```toml
[build]
  command = "npm run build"
  publish = ".next"

[[redirects]]
  from = "/api/*"
  to = "https://agrokongo-api.onrender.com/api/:splat"
  status = 200
  force = true

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### 1.3 Otimizar Next.js para produção

Atualizar `frontend/next.config.mjs`:
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // Para Netlify
  images: {
    unoptimized: true, // Netlify não suporta otimização de imagens
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
};

export default nextConfig;
```

### 1.4 Deploy no Netlify

```bash
# Instalar Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Deploy
cd frontend
netlify init
netlify deploy --prod
```

---

## 🐍 PARTE 2: Preparar Backend (Render/Railway)

### 2.1 Criar ficheiro de requisitos para produção

Criar `requirements-prod.txt`:
```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
Flask-SocketIO==5.3.5
psycopg2-binary==2.9.9
gunicorn==21.2.0
python-dotenv==1.0.0
Pillow==10.1.0
celery==5.3.4
redis==5.0.1
```

### 2.2 Criar Procfile (para Render)

Criar `Procfile`:
```
web: gunicorn run:app --workers 2 --threads 4 --timeout 120
worker: celery -A celery_worker.celery worker --loglevel=info
```

### 2.3 Criar render.yaml

Criar `render.yaml`:
```yaml
services:
  - type: web
    name: agrokongo-api
    env: python
    buildCommand: "pip install -r requirements-prod.txt"
    startCommand: "gunicorn run:app"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: agrokongo-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: REDIS_URL
        fromService:
          name: agrokongo-redis
          type: redis
          property: connectionString

databases:
  - name: agrokongo-db
    databaseName: agrokongo
    user: agrokongo

  - name: agrokongo-redis
    type: redis
```

### 2.4 Atualizar config.py para produção

```python
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS
    CORS_ORIGINS = [
        'https://agrokongo.netlify.app',
        'https://www.agrokongo.ao'
    ]
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # Celery
    CELERY_BROKER_URL = os.environ.get('REDIS_URL')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL')
```

---

## 🗄️ PARTE 3: Base de Dados (Supabase)

### 3.1 Criar projeto no Supabase
1. Aceder a https://supabase.com
2. Criar novo projeto
3. Copiar connection string

### 3.2 Executar migrações

```bash
# Localmente, apontando para Supabase
export DATABASE_URL="postgresql://user:pass@db.supabase.co:5432/postgres"
flask db upgrade
```

---

## 📸 PARTE 4: Storage (Cloudinary)

### 4.1 Configurar Cloudinary

```python
# app/utils/storage.py
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
)

def upload_image(file, folder):
    result = cloudinary.uploader.upload(
        file,
        folder=f"agrokongo/{folder}",
        transformation=[
            {'width': 1200, 'height': 1200, 'crop': 'limit'},
            {'quality': 'auto:good'}
        ]
    )
    return result['secure_url']
```

---

## ✅ CHECKLIST DE DEPLOY

### Segurança
- [ ] Todas as SECRET_KEY são únicas e seguras
- [ ] CORS configurado corretamente
- [ ] HTTPS ativado em todos os serviços
- [ ] Variáveis sensíveis em variáveis de ambiente
- [ ] Rate limiting ativado

### Performance
- [ ] Imagens otimizadas (WebP)
- [ ] CDN configurado (Netlify/Cloudinary)
- [ ] Cache configurado
- [ ] Compressão gzip ativada
- [ ] Database indexes criados

### Monitorização
- [ ] Logs configurados
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring
- [ ] Backup automático da BD

### Funcionalidades
- [ ] Migrações executadas
- [ ] Dados seed carregados
- [ ] Emails funcionando
- [ ] Pagamentos testados
- [ ] Celery tasks funcionando

---

## 🚀 Comandos de Deploy Rápido

### Frontend (Netlify)
```bash
cd frontend
npm run build
netlify deploy --prod
```

### Backend (Render)
```bash
git push origin main
# Render faz deploy automático
```

### Verificar saúde
```bash
# Frontend
curl https://agrokongo.netlify.app

# Backend
curl https://agrokongo-api.onrender.com/health
```

---

## 💰 Custos Estimados

| Serviço | Plano | Custo/mês |
|---------|-------|-----------|
| Netlify | Starter | €0 |
| Render | Free | €0 |
| Supabase | Free | €0 |
| Cloudinary | Free | €0 |
| **TOTAL** | | **€0** |

### Upgrade recomendado (produção real):
- Railway: $5/mês (melhor que Render Free)
- Supabase Pro: $25/mês (mais storage)
- Cloudinary Plus: $89/mês (mais transformações)

---

## 🆘 Troubleshooting

### Frontend não conecta ao Backend
- Verificar CORS no backend
- Confirmar NEXT_PUBLIC_API_URL correto
- Verificar redirects no netlify.toml

### Backend com erro 500
- Verificar logs: `render logs`
- Confirmar DATABASE_URL correto
- Verificar migrações executadas

### Imagens não carregam
- Verificar Cloudinary configurado
- Confirmar URLs públicas
- Verificar CORS do Cloudinary

---

## 📞 Próximos Passos

1. Criar contas nas plataformas
2. Configurar variáveis de ambiente
3. Fazer deploy do backend
4. Fazer deploy do frontend
5. Testar fluxo completo
6. Configurar domínio personalizado

**Quer que eu comece a implementar estas configurações?** 🚜
