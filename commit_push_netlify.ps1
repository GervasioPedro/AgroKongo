# Script para commit e push das correções do build Netlify

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Commit e Push - Correcoes Build Netlify" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para o diretório do repositório
Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "1. Verificando status do git..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "2. Adicionando arquivos modificados..." -ForegroundColor Yellow
git add frontend/src/pages/_app.js
git add frontend/src/pages/login.js
git add frontend/src/pages/register.js
git add frontend/src/pages/profile.js
git add frontend/src/pages/safra/[id].js
git add frontend/src/components/AdminLayout.js
git add frontend/src/components/ProtectedRoute.js
git add frontend/src/pages/styles/globals.css
git add frontend/netlify.toml
git add frontend/next.config.mjs

Write-Host ""
Write-Host "3. Verificando arquivos staged..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "4. Realizando commit..." -ForegroundColor Yellow
git commit -m "fix: corrigir caminhos relativos para build no Netlify

- Corrigir imports do useAuth em todos os arquivos pages/ e components/
- Criar pasta styles/ em pages/ com globals.css
- Atualizar netlify.toml com base = '.'
- Atualizar next.config.mjs com basePath explícito
- Resolver erro: Module not found: Can't resolve '../styles/globals.css'
- Resolver erro: Module not found: Can't resolve '../hooks/useAuth'

Arquivos corrigidos:
- frontend/src/pages/_app.js
- frontend/src/pages/login.js
- frontend/src/pages/register.js
- frontend/src/pages/profile.js
- frontend/src/pages/safra/[id].js
- frontend/src/components/AdminLayout.js
- frontend/src/components/ProtectedRoute.js

Fixes: Build error no Netlify deployment"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Commit realizado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "5. Fazendo push para o remoto..." -ForegroundColor Yellow
    
    # Tentar fazer push
    git push
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Push realizado com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "O Netlify irá rebuildar automaticamente em alguns minutos." -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "⚠️  Erro ao fazer push. Verifique suas credenciais." -ForegroundColor Red
        Write-Host ""
        Write-Host "Você pode fazer o push manualmente com: git push" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "⚠️  Erro ao realizar commit. Verifique se há alterações." -ForegroundColor Red
    Write-Host ""
    Write-Host "Se não há alterações, execute: git status" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
