# Script para corrigir remote do GitHub

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Corrigir Remote do GitHub" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "1. Verificando remote atual..." -ForegroundColor Yellow
$remoteUrl = git remote get-url origin 2>$null
if ($remoteUrl) {
    Write-Host "Remote atual: $remoteUrl" -ForegroundColor Red
} else {
    Write-Host "Nenhum remote configurado" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "2. Opções de URL para o repositório:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opção A - HTTPS (Recomendado para Windows):" -ForegroundColor Yellow
Write-Host "  https://github.com/GervaioPedro/AgroKongo.git" -ForegroundColor Gray
Write-Host ""
Write-Host "Opção B - SSH (Se tiver chave SSH configurada):" -ForegroundColor Yellow
Write-Host "  git@github.com:GervaioPedro/AgroKongo.git" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Qual URL deseja usar?" -ForegroundColor Cyan
Write-Host "  1 - HTTPS (https://github.com/GervaioPedro/AgroKongo.git)" -ForegroundColor White
Write-Host "  2 - SSH (git@github.com:GervaioPedro/AgroKongo.git)" -ForegroundColor White
Write-Host "  3 - Outra URL" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Escolha uma opção (1/2/3)"

if ($choice -eq "1") {
    $newUrl = "https://github.com/GervaioPedro/AgroKongo.git"
} elseif ($choice -eq "2") {
    $newUrl = "git@github.com:GervaioPedro/AgroKongo.git"
} else {
    $newUrl = Read-Host "Digite a URL completa do repositório"
}

Write-Host ""
Write-Host "4. Atualizando remote para: $newUrl" -ForegroundColor Yellow

# Remover remote antigo se existir
git remote remove origin 2>$null

# Adicionar novo remote
git remote add origin $newUrl

Write-Host ""
Write-Host "5. Verificando se funcionou..." -ForegroundColor Yellow
git remote -v

Write-Host ""
Write-Host "6. Testando conexão com GitHub..." -ForegroundColor Yellow
git fetch --dry-run 2>&1 | Tee-Object -Variable fetchResult

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Conexão bem-sucedida!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Agora você pode fazer o push com:" -ForegroundColor Cyan
    Write-Host "  git push -u origin main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Ou se a branch for master:" -ForegroundColor Gray
    Write-Host "  git push -u origin master" -ForegroundColor Gray
} else {
    Write-Host "❌ Erro ao conectar" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possíveis problemas:" -ForegroundColor Yellow
    Write-Host "  - Repositório não existe no GitHub" -ForegroundColor Gray
    Write-Host "  - Você não tem permissão de acesso" -ForegroundColor Gray
    Write-Host "  - Credenciais expiradas" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Verifique no GitHub se o repositório existe:" -ForegroundColor Cyan
    Write-Host "  https://github.com/GervaioPedro/AgroKongo" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
