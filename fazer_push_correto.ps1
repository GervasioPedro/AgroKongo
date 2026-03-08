# Script para fazer push com autenticação correta

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Push para GitHub - Autenticação Correta" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "⚠️  ATENÇÃO: NÃO cole o token diretamente no PowerShell!" -ForegroundColor Red
Write-Host ""
Write-Host "O token deve ser usado como SENHA quando o Git solicitar." -ForegroundColor Yellow
Write-Host ""

Write-Host "1. Verificando arquivos para commit..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "2. Adicionando todos os arquivos modificados..." -ForegroundColor Yellow
git add .

Write-Host ""
Write-Host "3. Fazendo commit..." -ForegroundColor Yellow
git commit -m "fix: corrigir caminhos relativos para build no Netlify"

Write-Host ""
Write-Host "4. Configurando para usar credenciais salvas..." -ForegroundColor Yellow
git config --global credential.helper wincred

Write-Host ""
Write-Host "5. Testando conexão com GitHub..." -ForegroundColor Yellow
git fetch origin 2>&1 | Tee-Object -Variable fetchResult

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Falha na autenticação. Limpando credenciais antigas..." -ForegroundColor Red
    git credential-manager erase
    cmdkey /delete:git:https://github.com 2>$null
    
    Write-Host ""
    Write-Host "✅ Credenciais limpas. Tente o push novamente." -ForegroundColor Green
    Write-Host ""
    Write-Host "Agora execute:" -ForegroundColor Cyan
    Write-Host "  git push -u origin main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Quando aparecer a janela de login:" -ForegroundColor Yellow
    Write-Host "  Username: GervaioPedro" -ForegroundColor White
    Write-Host "  Password: [seu token COMPLETO]" -ForegroundColor White
    Write-Host ""
    Write-Host "✅ Marque 'Salvar' para não precisar digitar novamente!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✅ Conexão bem-sucedida!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Fazendo push..." -ForegroundColor Yellow
    git push -u origin main
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
