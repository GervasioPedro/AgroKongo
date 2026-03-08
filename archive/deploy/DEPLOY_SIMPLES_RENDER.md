# 🚀 Deploy Simplificado - Só Render

## ✅ Tudo numa plataforma (mais fácil!)

### Passo 1: Criar conta no Render
1. Aceder: https://render.com
2. Criar conta com GitHub
3. ✅ Gratuito

### Passo 2: Deploy do Backend
1. No Render Dashboard:
   - Clicar "New +" → "Web Service"
   - Conectar: `GervasioPedro/AgroKongo`
   - Configurar:
     ```
     Name: agrokongo
     Branch: main
     Root Directory: (deixar vazio)
     Build Command: pip install -r requirements.txt
     Start Command: gunicorn run:app
     ```

2. Adicionar Base de Dados:
   - "New +" → "PostgreSQL"
   - Name: agrokongo-db
   - Copiar "Internal Database URL"

3. Variáveis de Ambiente (no Web Service):
   ```
   FLASK_ENV=production
   SECRET_KEY=<gerar: python -c "import secrets; print(secrets.token_hex(32))">
   DATABASE_URL=<colar Internal Database URL>
   ```

4. Deploy!
   - Clicar "Create Web Service"
   - Aguardar 5 minutos

### Passo 3: Executar Migrações
1. No Render Dashboard → Shell:
   ```bash
   flask db upgrade
   python seed.py
   ```

### Passo 4: Testar
```bash
# Abrir no navegador
https://agrokongo.onrender.com

# Fazer login
Telemovel: 942050656
Senha: AgroAdmin2026
```

---

## 💰 Custo: €0/mês

---

## ⚠️ Limitações do Plano Gratuito

- **Cold Start**: Após 15min sem uso, demora ~30s a acordar
- **750h/mês**: Suficiente para 1 serviço 24/7
- **512MB RAM**: Suficiente para começar

---

## 🔄 Quando Separar?

Só precisa de Netlify + Render + Supabase quando:
- Tiver >1000 utilizadores/dia
- Precisar de CDN global
- Quiser melhor performance

**Para começar: Só Render é suficiente!** ✅

---

## 🆘 Problemas?

### Erro ao fazer deploy
```bash
# Ver logs
render logs

# Verificar variáveis
render env
```

### Site não abre
- Aguardar 30s (cold start)
- Verificar logs no Dashboard
- Confirmar DATABASE_URL correto

---

## 📞 Próximo Passo

1. Criar conta no Render
2. Seguir Passo 2 acima
3. Testar aplicação

**É só isso!** 🎉
