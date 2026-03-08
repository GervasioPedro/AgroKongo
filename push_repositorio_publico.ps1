# Script para verificar se repositório agora é público e fazer push

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Verificar Repositório Público e Push" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "📝 Você já mudou o repositório para PÚBLICO no GitHub?" -ForegroundColor Yellow
Write-Host ""
$answer = Read-Host "Digite 'S' para SIM ou 'N' para NÃO"

if ($answer -eq "S" -or $answer -eq "s") {
    Write-Host ""
    Write-Host "✅ Ótimo! Vamos testar se agora funciona..." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Como tornar o repositório PÚBLICO:" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Acesse: https://github.com/GervaioPedro/AgroKongo" -ForegroundColor White
    Write-Host "2. Clique na aba 'Settings' (Configurações)" -ForegroundColor White
    Write-Host "3. Role até o final da página" -ForegroundColor White
    Write-Host "4. Em 'Danger Zone', clique em 'Change visibility'" -ForegroundColor White
    Write-Host "5. Selecione 'Make public'" -ForegroundColor White
    Write-Host "6. Digite o nome do repositório para confirmar" -ForegroundColor White
    Write-Host "7. Clique em 'I understand, make this repository public'" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Atenção: Qualquer pessoa poderá ver seu código!" -ForegroundColor Red
    Write-Host ""
    
    $done = Read-Host "Já fez isso? (S/N)"
    
    if ($done -ne "S" -and $done -ne "s") {
        Write-Host ""
        Write-Host "Volte aqui quando tiver feito a mudança!" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Fazendo Commit e Push" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Verificando status..." -ForegroundColor Yellow
git status --short

Write-Host ""
Write-Host "2. Adicionando todos os arquivos..." -ForegroundColor Yellow
git add -A

Write-Host ""
Write-Host "3. Fazendo commit..." -ForegroundColor Yellow
$hasChanges = git diff-index --quiet HEAD
if ($hasChanges) {
    git commit -m "fix: corrigir caminhos relativos para build no Netlify
    
- Corrigir imports do useAuth em pages/ e components/
- Criar pasta styles/ em pages/ com globals.css
- Atualizar netlify.toml e next.config.mjs
- Resolver erros de build no Netlify"
    Write-Host "✅ Commit realizado!" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Sem mudanças para commitar" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "4. Verificando remote..." -ForegroundColor Yellow
$currentRemote = git remote get-url origin 2>$null
if ($currentRemote) {
    Write-Host "Remote: $currentRemote" -ForegroundColor Cyan
} else {
    Write-Host "❌ Nenhum remote configurado!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "5. Testando acesso ao repositório..." -ForegroundColor Yellow
try {
    $testResult = git ls-remote $currentRemote 2>&1 | Select-Object -First 1
    
    if ($testResult -like "*Repository not found*") {
        Write-Host "❌ Ainda não consigo acessar o repositório!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Possíveis problemas:" -ForegroundColor Yellow
        Write-Host "  1. Repositório ainda está privado" -ForegroundColor White
        Write-Host "  2. URL do remote está errada" -ForegroundColor White
        Write-Host "  3. Repositório não existe" -ForegroundColor White
        Write-Host ""
        Write-Host "URL atual: $currentRemote" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Verifique no navegador: https://github.com/GervaioPedro/AgroKongo" -ForegroundColor Yellow
        exit 1
    } elseif ($testResult) {
        Write-Host "✅ Repositório acessível!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Não foi possível verificar" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "6. Fazendo push..." -ForegroundColor Yellow

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 PUSH REALIZADO COM SUCESSO!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos passos:" -ForegroundColor Cyan
    Write-Host "  1. Verifique no GitHub: https://github.com/GervaioPedro/AgroKongo" -ForegroundColor White
    Write-Host "  2. O Netlify vai rebuildar automaticamente" -ForegroundColor White
    Write-Host "  3. Monitore o deploy no Netlify" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Falha no push" -ForegroundColor Red
    Write-Host ""
    Write-Host "Se pediu senha e falhou, tente:" -ForegroundColor Yellow
    Write-Host "  - Usar token do GitHub como senha" -ForegroundColor White
    Write-Host "  - Ou mude o repositório para público" -ForegroundColor White
}

Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
