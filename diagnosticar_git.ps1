# Script para diagnosticar problemas com Git/GitHub

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Diagnóstico Git/GitHub" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "1. Verificando se é um repositório git..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "✅ Diretório .git encontrado" -ForegroundColor Green
} else {
    Write-Host "❌ NÃO é um repositório git!" -ForegroundColor Red
    Write-Host "Inicialize com: git init" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "2. Status atual do repositório..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "3. Verificando remote configurado..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl) {
    Write-Host "✅ Remote 'origin' configurado: $remoteUrl" -ForegroundColor Green
} else {
    Write-Host "❌ Nenhum remote configurado!" -ForegroundColor Red
    Write-Host "Adicione com: git remote add origin <URL_DO_REPOSITORIO>" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "4. Verificando branch atual..." -ForegroundColor Yellow
$branch = git branch --show-current
Write-Host "Branch atual: $branch" -ForegroundColor Cyan

Write-Host ""
Write-Host "5. Testando conexão com GitHub..." -ForegroundColor Yellow
git fetch --dry-run 2>&1 | Tee-Object -Variable fetchResult
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Conexão com GitHub bem-sucedida" -ForegroundColor Green
} else {
    Write-Host "❌ Erro de conexão com GitHub" -ForegroundColor Red
    Write-Host "Verifique:" -ForegroundColor Yellow
    Write-Host "  - Credenciais (git config --global credential.helper store)" -ForegroundColor Gray
    Write-Host "  - SSH keys ou token de acesso" -ForegroundColor Gray
    Write-Host "  - URL do remote está correta" -ForegroundColor Gray
}

Write-Host ""
Write-Host "6. Últimos commits locais..." -ForegroundColor Yellow
git log --oneline -5

Write-Host ""
Write-Host "7. Verificando se há commits não enviados..." -ForegroundColor Yellow
git status -sb

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Próximos Passos Sugeridos:" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Se houver arquivos modificados:" -ForegroundColor Yellow
Write-Host "  git add ." -ForegroundColor Gray
Write-Host "  git commit -m 'mensagem do commit'" -ForegroundColor Gray
Write-Host "  git push -u origin $branch" -ForegroundColor Gray
Write-Host ""
Write-Host "Se o remote estiver errado:" -ForegroundColor Yellow
Write-Host "  git remote set-url origin <URL_CORRETA>" -ForegroundColor Gray
Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
