# ✅ Checklist de Deploy Profissional

## 📋 Ordem de Execução

```
1. Supabase (Base de Dados)
   ↓
2. Render (Backend)
   ↓
3. Netlify (Frontend)
```

---

## 🗄️ FASE 1: Supabase (5 min)

- [ ] Criar conta em https://supabase.com
- [ ] Criar novo projeto "agrokongo"
- [ ] Escolher região: Europe (Frankfurt)
- [ ] Criar senha forte para DB
- [ ] Aguardar projeto ficar pronto (2 min)
- [ ] Copiar Connection String (Settings → Database)
- [ ] Guardar em local seguro

**Connection String:**
```
postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
```

---

## 🐍 FASE 2: Render Backend (10 min)

### 2.1 Preparação Local

- [ ] Gerar SECRET_KEY:
  ```bash
  python gerar_secret_key.py
  ```
- [ ] Copiar SECRET_KEY gerada

### 2.2 Criar Web Service

- [ ] Aceder https://dashboard.render.com
- [ ] New + → Web Service
- [ ] Conectar GitHub: `GervasioPedro/AgroKongo`
- [ ] Configurar:
  - Name: `agrokongo-api`
  - Region: `Frankfurt`
  - Branch: `main`
  - Build: `pip install -r requirements.txt`
  - Start: `gunicorn run:app --workers 2 --threads 4 --timeout 120`

### 2.3 Criar Redis

- [ ] New + → Redis
- [ ] Name: `agrokongo-redis`
- [ ] Region: `Frankfurt`
- [ ] Copiar Internal Redis URL

### 2.4 Variáveis de Ambiente

Adicionar no Web Service:

- [ ] `FLASK_ENV=production`
- [ ] `SECRET_KEY=[copiar da gerada]`
- [ ] `DATABASE_URL=[copiar do Supabase]`
- [ ] `REDIS_URL=[copiar do Redis]`
- [ ] `CORS_ORIGINS=https://agrokongo.netlify.app`

### 2.5 Deploy e Migrações

- [ ] Clicar "Create Web Service"
- [ ] Aguardar deploy (5-7 min)
- [ ] Abrir Shell no Render
- [ ] Executar:
  ```bash
  flask db upgrade
  python seed.py
  ```

### 2.6 Testar Backend

- [ ] Abrir: `https://agrokongo-api.onrender.com/health`
- [ ] Verificar resposta:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "redis": "connected"
  }
  ```

**✅ Backend URL:** `https://agrokongo-api.onrender.com`

---

## 🌐 FASE 3: Netlify Frontend (5 min)

### 3.1 Criar Site

- [ ] Aceder https://app.netlify.com
- [ ] Add new site → Import project
- [ ] Conectar GitHub: `GervasioPedro/AgroKongo`
- [ ] Configurar:
  - Base directory: `frontend`
  - Build: `npm run build`
  - Publish: `frontend/.next`

### 3.2 Variáveis de Ambiente

- [ ] `NEXT_PUBLIC_API_URL=https://agrokongo-api.onrender.com`
- [ ] `NEXT_PUBLIC_APP_URL=https://agrokongo.netlify.app`
- [ ] `NODE_VERSION=18`

### 3.3 Deploy

- [ ] Clicar "Deploy site"
- [ ] Aguardar build (3-5 min)
- [ ] Copiar URL gerada

### 3.4 Atualizar CORS

- [ ] Voltar ao Render
- [ ] Atualizar `CORS_ORIGINS` com URL real do Netlify
- [ ] Fazer redeploy do backend

### 3.5 Testar Frontend

- [ ] Abrir URL do Netlify
- [ ] Fazer login:
  - Telemovel: `942050656`
  - Senha: `AgroAdmin2026`
- [ ] Verificar dashboard carrega
- [ ] Testar navegação

**✅ Frontend URL:** `https://seu-site.netlify.app`

---

## 🎯 Verificação Final

### Conectividade

- [ ] Frontend carrega sem erros
- [ ] Login funciona
- [ ] API responde (Network tab)
- [ ] Imagens carregam
- [ ] Navegação funciona

### Performance

- [ ] Lighthouse Score > 80
- [ ] Tempo de carregamento < 3s
- [ ] Sem erros no console

### Segurança

- [ ] HTTPS ativo (cadeado verde)
- [ ] CORS configurado
- [ ] Headers de segurança ativos
- [ ] Variáveis sensíveis em ENV

---

## 📊 URLs Finais

| Serviço | URL | Status |
|---------|-----|--------|
| **Frontend** | https://agrokongo.netlify.app | ⏳ |
| **Backend** | https://agrokongo-api.onrender.com | ⏳ |
| **Health** | https://agrokongo-api.onrender.com/health | ⏳ |
| **Database** | Supabase Dashboard | ⏳ |

---

## 🔄 Deploy Contínuo

Após configuração inicial:

```bash
# Fazer alterações
git add .
git commit -m "Nova funcionalidade"
git push origin main

# Deploy automático:
# ✅ Render detecta e faz deploy do backend
# ✅ Netlify detecta e faz deploy do frontend
```

---

## 💰 Custos

| Serviço | Plano | Custo |
|---------|-------|-------|
| Netlify | Starter | €0 |
| Render | Free | €0 |
| Supabase | Free | €0 |
| **TOTAL** | | **€0/mês** |

---

## 🆘 Suporte

### Documentação
- `GUIA_RENDER.md` - Detalhes do backend
- `GUIA_NETLIFY.md` - Detalhes do frontend
- `DEPLOY_PRODUCAO.md` - Guia completo

### Problemas Comuns
1. **Backend não inicia**: Ver logs no Render
2. **Frontend não conecta**: Verificar CORS
3. **Erro 500**: Verificar DATABASE_URL

---

## 🎉 Parabéns!

Quando todos os checkboxes estiverem marcados, o AgroKongo estará em produção! 🚜🇦🇴

**Próximo passo:** Testar todas as funcionalidades em produção.
