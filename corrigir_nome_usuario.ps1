# Script para corrigir URL do remote com nome correto

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Corrigir URL do Remote - Nome Correto" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "📝 Corrigindo nome do usuário no GitHub..." -ForegroundColor Yellow
Write-Host ""
Write-Host "De: GervaioPedro (ERRADO)" -ForegroundColor Red
Write-Host "Para: GervasioPedro (CORRETO)" -ForegroundColor Green
Write-Host ""

# URL antiga (errada)
$oldUrl = git remote get-url origin 2>$null
Write-Host "URL atual: $oldUrl" -ForegroundColor Cyan
Write-Host ""

# Nova URL (correta)
$newUrl = "https://github.com/GervasioPedro/AgroKongo.git"
Write-Host "Nova URL: $newUrl" -ForegroundColor Green
Write-Host ""

Write-Host "1. Removendo remote antigo..." -ForegroundColor Yellow
git remote remove origin

Write-Host ""
Write-Host "2. Adicionando novo remote com URL correta..." -ForegroundColor Yellow
git remote add origin $newUrl

Write-Host ""
Write-Host "3. Verificando se funcionou..." -ForegroundColor Yellow
git remote -v

Write-Host ""
Write-Host "4. Testando conexão com GitHub..." -ForegroundColor Yellow
git ls-remote $newUrl 2>&1 | Select-Object -First 5

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Conexão bem-sucedida!" -ForegroundColor Green
    Write-Host ""
    Write-Host "5. Fazendo push..." -ForegroundColor Yellow
    
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 PUSH REALIZADO COM SUCESSO!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Verifique seu repositório:" -ForegroundColor Cyan
        Write-Host "  https://github.com/GervasioPedro/AgroKongo" -ForegroundColor White
        Write-Host ""
        Write-Host "O Netlify vai rebuildar automaticamente!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️  Push falhou, mas a URL está correta agora." -ForegroundColor Yellow
        Write-Host "Tente novamente: git push -u origin main" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "❌ Repositório não encontrado na nova URL" -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique:" -ForegroundColor Yellow
    Write-Host "  1. O repositório existe em https://github.com/GervasioPedro/AgroKongo ?" -ForegroundColor White
    Write-Host "  2. Se não existir, crie um novo repositório nesse nome" -ForegroundColor White
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
