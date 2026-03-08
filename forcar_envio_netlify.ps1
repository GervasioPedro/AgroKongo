# Script para forçar envio das correções do Netlify

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Forçar Envio das Correções" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "⚠️  O Netlify ainda está com erros de build!" -ForegroundColor Red
Write-Host ""
Write-Host "Isso significa que os arquivos NÃO foram atualizados no GitHub." -ForegroundColor Yellow
Write-Host ""

Write-Host "1. Verificando status detalhado..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "2. Verificando se os arquivos foram modificados LOCALMENTE..." -ForegroundColor Yellow

$filesToCheck = @(
    "frontend/src/pages/_app.js",
    "frontend/src/pages/login.js",
    "frontend/src/pages/register.js",
    "frontend/src/pages/profile.js",
    "frontend/src/pages/safra/[id].js",
    "frontend/src/components/AdminLayout.js",
    "frontend/src/components/ProtectedRoute.js",
    "frontend/src/pages/styles/globals.css",
    "frontend/netlify.toml",
    "frontend/next.config.mjs"
)

$modifiedFiles = @()
foreach ($file in $filesToCheck) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Gray
        $modifiedFiles += $file
    } else {
        Write-Host "  ✗ $file (NÃO ENCONTRADO)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "3. Adicionando TODOS os arquivos modificados..." -ForegroundColor Yellow
git add -A --verbose

Write-Host ""
Write-Host "4. Verificando o que será commitado..." -ForegroundColor Yellow
git status --short

Write-Host ""
$confirm = Read-Host "Deseja fazer commit e push AGORA? (S/N)"

if ($confirm -eq "S" -or $confirm -eq "s") {
    Write-Host ""
    Write-Host "5. Fazendo commit..." -ForegroundColor Yellow
    
    git commit -m "fix: corrigir caminhos relativos para build no Netlify - ENVIO FORÇADO

Arquivos corrigidos:
- frontend/src/pages/_app.js: import '../styles/globals.css'
- frontend/src/pages/login.js: import '../../hooks/useAuth'
- frontend/src/pages/register.js: import '../../hooks/useAuth'
- frontend/src/pages/profile.js: import '../../hooks/useAuth'
- frontend/src/pages/safra/[id].js: import '../../hooks/useAuth'
- frontend/src/components/AdminLayout.js: import '../../hooks/useAuth'
- frontend/src/components/ProtectedRoute.js: import '../../hooks/useAuth'
- frontend/src/pages/styles/globals.css: NOVO ARQUIVO
- frontend/netlify.toml: base = '.'
- frontend/next.config.mjs: basePath = ''

Resolvendo erros do Netlify:
- Module not found: Can't resolve '../styles/globals.css'
- Module not found: Can't resolve '../hooks/useAuth'"

    Write-Host ""
    Write-Host "6. Verificando último commit..." -ForegroundColor Yellow
    git log --oneline -1
    
    Write-Host ""
    Write-Host "7. Fazendo push FORÇADO para o GitHub..." -ForegroundColor Yellow
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 PUSH REALIZADO COM SUCESSO!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Agora aguarde 2-3 minutos e verifique o Netlify:" -ForegroundColor Cyan
        Write-Host "  https://app.netlify.com/" -ForegroundColor White
        Write-Host ""
        Write-Host "O deploy automático deve começar em breve!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Push falhou novamente!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Tente manualmente:" -ForegroundColor Yellow
        Write-Host "  git push -u origin main" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "⚠️  Operação cancelada. Execute manualmente:" -ForegroundColor Red
    Write-Host "  git add -A" -ForegroundColor Gray
    Write-Host "  git commit -m 'fix: corrigir caminhos relativos para build no Netlify'" -ForegroundColor Gray
    Write-Host "  git push -u origin main" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
