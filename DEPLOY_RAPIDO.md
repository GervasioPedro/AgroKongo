# 🚀 Guia Rápido de Deploy - AgroKongo

## ⚡ Deploy em 10 Minutos

### Passo 1: Preparar Contas (5 min)

1. **Netlify** (Frontend)
   - Aceder: https://netlify.com
   - Criar conta com GitHub
   - ✅ Gratuito

2. **Render** (Backend)
   - Aceder: https://render.com
   - Criar conta com GitHub
   - ✅ Gratuito (com limitações)

3. **Supabase** (Base de Dados)
   - Aceder: https://supabase.com
   - Criar conta
   - Criar novo projeto
   - Copiar connection string
   - ✅ Gratuito (500MB)

### Passo 2: Deploy do Backend (3 min)

1. **No Render Dashboard:**
   - Clicar em "New +" → "Web Service"
   - Conectar repositório GitHub: `GervasioPedro/AgroKongo`
   - Configurar:
     ```
     Name: agrokongo-api
     Branch: main
     Build Command: pip install -r requirements.txt
     Start Command: gunicorn run:app
     ```

2. **Adicionar Variáveis de Ambiente:**
   ```
   FLASK_ENV=production
   SECRET_KEY=[gerar com: python -c "import secrets; print(secrets.token_hex(32))"]
   DATABASE_URL=[copiar do Supabase]
   CORS_ORIGINS=https://agrokongo.netlify.app
   ```

3. **Criar Base de Dados:**
   - No Render: "New +" → "PostgreSQL"
   - Name: agrokongo-db
   - Copiar Internal Database URL
   - Adicionar como DATABASE_URL no Web Service

4. **Executar Migrações:**
   ```bash
   # No Render Shell (ou localmente)
   flask db upgrade
   python seed.py  # Dados iniciais
   ```

### Passo 3: Deploy do Frontend (2 min)

1. **No Netlify Dashboard:**
   - Clicar em "Add new site" → "Import an existing project"
   - Conectar GitHub: `GervasioPedro/AgroKongo`
   - Configurar:
     ```
     Base directory: frontend
     Build command: npm run build
     Publish directory: frontend/.next
     ```

2. **Adicionar Variáveis de Ambiente:**
   ```
   NEXT_PUBLIC_API_URL=https://agrokongo-api.onrender.com
   NEXT_PUBLIC_APP_URL=https://agrokongo.netlify.app
   ```

3. **Deploy:**
   - Clicar em "Deploy site"
   - Aguardar 2-3 minutos

### Passo 4: Verificar (1 min)

```bash
# Testar Backend
curl https://agrokongo-api.onrender.com/health

# Testar Frontend
curl https://agrokongo.netlify.app

# Abrir no navegador
open https://agrokongo.netlify.app
```

---

## 🔧 Configurações Opcionais

### Domínio Personalizado

**Netlify:**
1. Settings → Domain management
2. Add custom domain: `www.agrokongo.ao`
3. Configurar DNS (A record ou CNAME)

**Render:**
1. Settings → Custom Domain
2. Add: `api.agrokongo.ao`

### SSL/HTTPS
✅ Automático no Netlify e Render (Let's Encrypt)

### Monitorização

**UptimeRobot** (Gratuito):
```
Monitor 1: https://agrokongo.netlify.app
Monitor 2: https://agrokongo-api.onrender.com/health
Interval: 5 minutos
```

---

## 🐛 Troubleshooting

### Backend não inicia
```bash
# Ver logs no Render
render logs

# Verificar variáveis
echo $DATABASE_URL
echo $SECRET_KEY
```

### Frontend não conecta ao Backend
1. Verificar CORS no backend (config.py)
2. Confirmar NEXT_PUBLIC_API_URL correto
3. Verificar redirects no netlify.toml

### Erro 500 no Backend
1. Ver logs: `render logs`
2. Verificar migrações: `flask db current`
3. Testar localmente primeiro

### Build falha no Netlify
1. Verificar package.json
2. Confirmar Node version (18+)
3. Ver build logs no Netlify

---

## 📊 Monitorização de Custos

### Plano Gratuito (Atual)
- Netlify: 100GB bandwidth/mês
- Render: 750h/mês (suficiente para 1 serviço 24/7)
- Supabase: 500MB storage, 2GB bandwidth

### Quando Upgrade?
- **Render → Paid ($7/mês)**: Quando tiver >1000 utilizadores/dia
- **Supabase → Pro ($25/mês)**: Quando BD >500MB
- **Cloudinary ($89/mês)**: Quando >25GB imagens

---

## 🔄 Deploy Contínuo

Após configuração inicial, cada `git push` faz deploy automático:

```bash
# Fazer alterações
git add .
git commit -m "Nova funcionalidade"
git push origin main

# Netlify e Render fazem deploy automático
# Aguardar 2-3 minutos
```

---

## ✅ Checklist Final

- [ ] Backend deployed e acessível
- [ ] Frontend deployed e acessível
- [ ] Base de dados criada e migrada
- [ ] Variáveis de ambiente configuradas
- [ ] CORS funcionando
- [ ] SSL/HTTPS ativo
- [ ] Health check respondendo
- [ ] Domínio personalizado (opcional)
- [ ] Monitorização configurada
- [ ] Backup automático ativo

---

## 🆘 Suporte

**Problemas?**
1. Verificar logs: Render Dashboard → Logs
2. Testar localmente primeiro
3. Verificar documentação: DEPLOY_PRODUCAO.md
4. GitHub Issues: https://github.com/GervasioPedro/AgroKongo/issues

**Recursos:**
- Render Docs: https://render.com/docs
- Netlify Docs: https://docs.netlify.com
- Supabase Docs: https://supabase.com/docs

---

🎉 **Parabéns! AgroKongo está em produção!** 🚜🇦🇴
