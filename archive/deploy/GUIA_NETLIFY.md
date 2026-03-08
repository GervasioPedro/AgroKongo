# 🌐 Configuração Netlify - Frontend

## Passo 1: Criar Site

1. Aceder: https://app.netlify.com
2. Clicar "Add new site" → "Import an existing project"
3. Conectar GitHub: `GervasioPedro/AgroKongo`
4. Configurar:

```yaml
Base directory: frontend
Build command: npm run build
Publish directory: frontend/.next
```

## Passo 2: Variáveis de Ambiente

Adicionar no Netlify (Site settings → Environment variables):

```env
# URL do Backend (copiar do Render)
NEXT_PUBLIC_API_URL=https://agrokongo-api.onrender.com

# URL do Frontend (atualizar depois do deploy)
NEXT_PUBLIC_APP_URL=https://agrokongo.netlify.app

# Node version
NODE_VERSION=18
```

## Passo 3: Deploy

1. Clicar "Deploy site"
2. Aguardar 3-5 minutos
3. Netlify gera URL automático: `https://random-name-123.netlify.app`

## Passo 4: Configurar Domínio Personalizado (Opcional)

1. Site settings → Domain management
2. Clicar "Add custom domain"
3. Adicionar: `agrokongo.netlify.app` ou `www.agrokongo.ao`
4. Seguir instruções de DNS

## Passo 5: Atualizar CORS no Backend

Voltar ao Render e atualizar variável CORS_ORIGINS:

```env
CORS_ORIGINS=https://seu-site.netlify.app,https://www.agrokongo.ao
```

## Passo 6: Testar

```bash
# Abrir no navegador
https://seu-site.netlify.app

# Testar login
Telemovel: 942050656
Senha: AgroAdmin2026
```

## ✅ Frontend Pronto!

URL: https://seu-site.netlify.app

## 🔄 Deploy Automático

Cada `git push` faz deploy automático:
- Backend: Render detecta e faz deploy
- Frontend: Netlify detecta e faz deploy

## 📊 Monitorização

### Netlify
- Analytics: Site settings → Analytics
- Logs: Deploys → Ver logs

### Render
- Logs: Dashboard → Logs
- Metrics: Dashboard → Metrics

## 🆘 Troubleshooting

### Frontend não conecta ao Backend

1. Verificar CORS no Render:
   ```env
   CORS_ORIGINS=https://seu-site.netlify.app
   ```

2. Verificar variável no Netlify:
   ```env
   NEXT_PUBLIC_API_URL=https://agrokongo-api.onrender.com
   ```

3. Testar API diretamente:
   ```bash
   curl https://agrokongo-api.onrender.com/health
   ```

### Erro 500 no Backend

1. Ver logs no Render
2. Verificar DATABASE_URL
3. Confirmar migrações: `flask db current`

### Build falha no Netlify

1. Ver logs de build
2. Verificar Node version (18)
3. Testar localmente: `cd frontend && npm run build`
