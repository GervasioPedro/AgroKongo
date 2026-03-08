# Script simplificado para push no GitHub

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Push GitHub - Método Simplificado" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "1. Verificando status..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "2. Adicionando TODOS os arquivos modificados..." -ForegroundColor Yellow
git add -A

Write-Host ""
Write-Host "3. Fazendo commit (se houver mudanças)..." -ForegroundColor Yellow
$hasChanges = git diff-index --quiet HEAD
if ($hasChanges) {
    git commit -m "fix: corrigir caminhos relativos para build no Netlify"
    Write-Host "✅ Commit realizado!" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Sem mudanças para commitar" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "4. Verificando remote atual..." -ForegroundColor Yellow
$currentRemote = git remote get-url origin 2>$null
if ($currentRemote) {
    Write-Host "Remote atual: $currentRemote" -ForegroundColor Cyan
} else {
    Write-Host "❌ Nenhum remote configurado!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "5. Testando se o repositório existe..." -ForegroundColor Yellow
try {
    # Tentar fazer fetch sem autenticar primeiro
    $testResult = git ls-remote $currentRemote 2>&1 | Select-Object -First 1
    
    if ($testResult -like "*Repository not found*") {
        Write-Host "❌ Repositório não encontrado ou você não tem acesso!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Verifique:" -ForegroundColor Yellow
        Write-Host "  1. O repositório existe no GitHub?" -ForegroundColor White
        Write-Host "  2. Você tem permissão de acesso?" -ForegroundColor White
        Write-Host "  3. A URL está correta?" -ForegroundColor White
        Write-Host ""
        Write-Host "URL atual: $currentRemote" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Para mudar a URL, execute:" -ForegroundColor Yellow
        Write-Host "  git remote set-url origin https://github.com/USUARIO/CORRETO.git" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "⚠️  Não foi possível verificar o repositório" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "6. Fazendo push..." -ForegroundColor Yellow
Write-Host "⚠️  Quando pedir credenciais:" -ForegroundColor Red
Write-Host "  Username: GervaioPedro" -ForegroundColor White
Write-Host "  Password: SEU TOKEN COMPLETO (ghp_...)" -ForegroundColor White
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ PUSH REALIZADO COM SUCESSO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "O Netlify vai rebuildar automaticamente em 1-2 minutos." -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "❌ Falha no push" -ForegroundColor Red
    Write-Host ""
    Write-Host "Tente novamente com:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
