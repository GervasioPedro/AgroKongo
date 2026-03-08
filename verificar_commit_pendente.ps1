# Script para verificar se commit foi feito e fazer push se necessário

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Verificar Commit e Push Pendente" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "1. Verificando status dos arquivos..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "2. Verificando últimos commits locais..." -ForegroundColor Yellow
git log --oneline -5

Write-Host ""
Write-Host "3. Verificando diferenças entre local e remoto..." -ForegroundColor Yellow
git log origin/main..main --oneline 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Não há commits pendentes de push" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⚠️  Há commits locais que não foram enviados!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Fazendo push agora..." -ForegroundColor Cyan
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 Push realizado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Falha no push" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "4. Verificando se há arquivos modificados não commitados..." -ForegroundColor Yellow
$uncommitted = git diff-index --quiet HEAD

if ($uncommitted) {
    Write-Host ""
    Write-Host "⚠️  Há arquivos modificados que NÃO foram commitados!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Arquivos alterados:" -ForegroundColor Yellow
    git status --short
    
    Write-Host ""
    $commit = Read-Host "Deseja fazer commit e push agora? (S/N)"
    
    if ($commit -eq "S" -or $commit -eq "s") {
        Write-Host ""
        Write-Host "Adicionando arquivos..." -ForegroundColor Yellow
        git add -A
        
        Write-Host ""
        Write-Host "Fazendo commit..." -ForegroundColor Yellow
        git commit -m "fix: corrigir caminhos relativos para build no Netlify
        
- Corrigir imports do useAuth em pages/ e components/
- Criar pasta styles/ em pages/ com globals.css
- Atualizar netlify.toml e next.config.mjs
- Resolver erros de build no Netlify"
        
        Write-Host ""
        Write-Host "Fazendo push..." -ForegroundColor Yellow
        git push -u origin main
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "🎉 SUCESSO! Tudo enviado para o GitHub!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Verifique seu repositório:" -ForegroundColor Cyan
            Write-Host "  https://github.com/GervasioPedro/AgroKongo" -ForegroundColor White
            Write-Host ""
            Write-Host "O Netlify vai rebuildar automaticamente em 1-2 minutos!" -ForegroundColor Green
        }
    }
} else {
    Write-Host ""
    Write-Host "✅ Todos os arquivos estão commitados" -ForegroundColor Green
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
