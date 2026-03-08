# Script para diagnosticar e corrigir problema do repositório

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Diagnóstico Completo do Repositório" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "🔍 VERIFICAÇÃO 1: O repositório existe no GitHub?" -ForegroundColor Yellow
Write-Host ""
Write-Host "Abra o navegador e acesse:" -ForegroundColor White
Write-Host "  https://github.com/GervaioPedro/AgroKongo" -ForegroundColor Cyan
Write-Host ""
Write-Host "O que você vê?" -ForegroundColor Yellow
Write-Host "  [1] Página do repositório com arquivos" -ForegroundColor White
Write-Host "  [2] Erro 404 - Page not found" -ForegroundColor White
Write-Host "  [3] Mensagem de acesso negado" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Digite o número (1/2/3)"

if ($choice -eq "2") {
    Write-Host ""
    Write-Host "❌ O repositório NÃO EXISTE!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Soluções possíveis:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Opção A - Criar novo repositório:" -ForegroundColor Cyan
    Write-Host "  1. Acesse: https://github.com/new" -ForegroundColor White
    Write-Host "  2. Nome: AgroKongo" -ForegroundColor White
    Write-Host "  3. Marque 'Public'" -ForegroundColor White
    Write-Host "  4. Clique em 'Create repository'" -ForegroundColor White
    Write-Host ""
    
    $create = Read-Host "Quer criar um novo repositório? (S/N)"
    if ($create -eq "S" -or $create -eq "s") {
        Write-Host ""
        Write-Host "Depois de criar, execute estes comandos:" -ForegroundColor Green
        Write-Host ""
        Write-Host "# Remover remote antigo" -ForegroundColor Gray
        Write-Host "git remote remove origin" -ForegroundColor White
        Write-Host ""
        Write-Host "# Adicionar novo remote (substitua SEU_USUARIO)" -ForegroundColor Gray
        Write-Host "git remote add origin https://github.com/SEU_USUARIO/AgroKongo.git" -ForegroundColor White
        Write-Host ""
        Write-Host "# Fazer push" -ForegroundColor Gray
        Write-Host "git push -u origin main" -ForegroundColor White
        exit 0
    }
    
} elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "⚠️  Repositório existe mas está PRIVADO!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para tornar PÚBLICO:" -ForegroundColor Yellow
    Write-Host "  1. Acesse: https://github.com/GervaioPedro/AgroKongo/settings" -ForegroundColor White
    Write-Host "  2. Role até 'Danger Zone'" -ForegroundColor White
    Write-Host "  3. Clique em 'Change visibility'" -ForegroundColor White
    Write-Host "  4. Escolha 'Make public'" -ForegroundColor White
    Write-Host ""
    Write-Host "Depois disso, tente o push novamente!" -ForegroundColor Green
    exit 0
    
} elseif ($choice -eq "1") {
    Write-Host ""
    Write-Host "✅ Repositório existe e é público!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Mas o Git ainda não consegue acessar..." -ForegroundColor Yellow
    Write-Host "Vamos verificar o remote:" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🔍 VERIFICAÇÃO 2: URL do remote está correta?" -ForegroundColor Yellow
Write-Host ""

$currentRemote = git remote get-url origin 2>$null
if ($currentRemote) {
    Write-Host "Remote atual: $currentRemote" -ForegroundColor Cyan
    
    # Verificar se tem barra extra no final
    if ($currentRemote -match "/$") {
        Write-Host ""
        Write-Host "⚠️  Atenção: URL tem barra '/' no final!" -ForegroundColor Yellow
        Write-Host "Isso pode causar problemas." -ForegroundColor Yellow
        
        $fixUrl = Read-Host "Deseja corrigir a URL? (S/N)"
        if ($fixUrl -eq "S" -or $fixUrl -eq "s") {
            $correctUrl = $currentRemote.TrimEnd("/")
            Write-Host ""
            Write-Host "Corrigindo de '$currentRemote' para '$correctUrl'" -ForegroundColor Green
            git remote set-url origin $correctUrl
            Write-Host "✅ URL corrigida!" -ForegroundColor Green
            
            Write-Host ""
            Write-Host "Tentando push agora..." -ForegroundColor Yellow
            git push -u origin main
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "🎉 SUCESSO!" -ForegroundColor Green
                exit 0
            }
        }
    }
} else {
    Write-Host "❌ Nenhum remote configurado!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Para adicionar:" -ForegroundColor Yellow
    Write-Host "  git remote add origin https://github.com/GervaioPedro/AgroKongo.git" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "🔍 VERIFICAÇÃO 3: Testando conexão direta..." -ForegroundColor Yellow
Write-Host ""

# Tentar conectar sem autenticação
try {
    $result = git ls-remote $currentRemote 2>&1
    
    if ($result -like "*Repository not found*") {
        Write-Host "❌ GitHub diz que repositório não existe!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Isso confirma que o problema é:" -ForegroundColor Yellow
        Write-Host "  - Repositório não existe, OU" -ForegroundColor White
        Write-Host "  - Está privado E você não autenticou, OU" -ForegroundColor White
        Write-Host "  - URL está errada" -ForegroundColor White
    } else {
        Write-Host "✅ Conexão funcionou!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Fazendo push..." -ForegroundColor Yellow
        git push -u origin main
    }
} catch {
    Write-Host "❌ Erro ao testar conexão" -ForegroundColor Red
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Resumo:" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Se nada funcionou, verifique:" -ForegroundColor Yellow
Write-Host "  1. Você está logado na conta CERTA no GitHub?" -ForegroundColor White
Write-Host "  2. O repositório realmente existe?" -ForegroundColor White
Write-Host "  3. A URL está exata (case-sensitive)?" -ForegroundColor White
Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
