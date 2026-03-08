# Script para configurar autenticação com GitHub (Repositório Privado)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Configurar Autenticação - GitHub Privado" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "C:\Users\Madalena Fernandes\Desktop\GSP\agrokongoVS"

Write-Host "📋 Opções de Autenticação:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Token Pessoal do GitHub (PAT) - RECOMENDADO" -ForegroundColor Cyan
Write-Host "   - Mais seguro" -ForegroundColor Gray
Write-Host "   - Não expira a cada login" -ForegroundColor Gray
Write-Host "   - Permissões controladas" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  Credenciais do Windows (Username/Senha)" -ForegroundColor Cyan
Write-Host "   - Mais simples" -ForegroundColor Gray
Write-Host "   - Pode pedir toda vez" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  SSH Key" -ForegroundColor Cyan
Write-Host "   - Muito seguro" -ForegroundColor Gray
Write-Host "   - Configuração única" -ForegroundColor Gray
Write-Host ""

$choice = Read-Host "Escolha o método de autenticação (1/2/3)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Opção 1: Token Pessoal do GitHub (PAT)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 Como criar seu token:" -ForegroundColor Yellow
    Write-Host "1. Acesse: https://github.com/settings/tokens" -ForegroundColor White
    Write-Host "2. Clique em 'Generate new token (classic)' ou 'Generate new token'" -ForegroundColor White
    Write-Host "3. Dê um nome: 'AgroKongo Deploy'" -ForegroundColor White
    Write-Host "4. Expiração: 90 dias (ou mais)" -ForegroundColor White
    Write-Host "5. Marque as permissões:" -ForegroundColor White
    Write-Host "   ✅ repo (Full control of private repositories)" -ForegroundColor Green
    Write-Host "   ✅ workflow (Se usar GitHub Actions)" -ForegroundColor Green
    Write-Host "6. Clique em 'Generate token' no final da página" -ForegroundColor White
    Write-Host "7. COPIE O TOKEN (você só vê uma vez!)" -ForegroundColor Red
    Write-Host ""
    
    $token = Read-Host "Cole seu token aqui (não será visível)"
    
    if ($token) {
        # Salvar credencial temporariamente
        $username = Read-Host "Digite seu usuário do GitHub"
        
        # Configurar Git Credential Manager
        git config --global credential.helper wincred
        
        # Forçar nova autenticação
        git credential-manager erase
        cmdkey /delete:git:https://github.com 2>$null
        
        Write-Host ""
        Write-Host "✅ Credenciais antigas limpas!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Agora faça o push e quando pedir senha, cole o TOKEN:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "git push -u origin main" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Username: $username" -ForegroundColor Cyan
        Write-Host "Password: [cole o token aqui]" -ForegroundColor Cyan
    }
    
} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Opção 2: Credenciais do Windows" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Limpar credenciais antigas
    git credential-manager erase
    cmdkey /delete:git:https://github.com 2>$null
    
    Write-Host "✅ Credenciais antigas limpas!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Agora faça o push e insira suas credenciais:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "git push -u origin main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Quando pedir:" -ForegroundColor Cyan
    Write-Host "  Username: seu-usuário-github" -ForegroundColor White
    Write-Host "  Password: sua-senha-do-github (ou token)" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Dica: Marque 'Salvar' quando o Windows perguntar" -ForegroundColor Yellow
    
} elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Opção 3: Chave SSH" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Verificar se já existe chave SSH
    $sshDir = "$env:USERPROFILE\.ssh"
    $pubKey = "$sshDir\id_ed25519.pub"
    
    if (Test-Path $pubKey) {
        Write-Host "✅ Chave SSH já existe: $pubKey" -ForegroundColor Green
        Write-Host ""
        Write-Host "Conteúdo da chave pública:" -ForegroundColor Yellow
        Get-Content $pubKey
        Write-Host ""
        Write-Host "Adicione esta chave em: https://github.com/settings/keys" -ForegroundColor Cyan
    } else {
        Write-Host "🔑 Gerando nova chave SSH..." -ForegroundColor Yellow
        ssh-keygen -t ed25519 -C "seu-email@exemplo.com"
        
        Write-Host ""
        Write-Host "Chave gerada! Agora adicione no GitHub:" -ForegroundColor Green
        Write-Host "1. Copie o conteúdo de: $pubKey" -ForegroundColor White
        Write-Host "2. Vá em: https://github.com/settings/keys" -ForegroundColor White
        Write-Host "3. Clique em 'New SSH key'" -ForegroundColor White
        Write-Host "4. Cole a chave e salve" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "Depois de adicionar a chave no GitHub, mude o remote para SSH:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "git remote set-url origin git@github.com:GervaioPedro/AgroKongo.git" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Teste a conexão:" -ForegroundColor Yellow
    Write-Host "ssh -T git@github.com" -ForegroundColor Gray
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Próximos Passos:" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Configure a autenticação conforme escolhido acima" -ForegroundColor White
Write-Host "2. Teste com: git fetch" -ForegroundColor Gray
Write-Host "3. Faça o push: git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
