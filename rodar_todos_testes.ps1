# Script para rodar todos os testes do AgroKongo
# Executa em ordem: unitários → integração → automation

Write-Host "🚀 Iniciando suite completa de testes do AgroKongo" -ForegroundColor Green
Write-Host ""

# Configurar variáveis de ambiente para testes
$env:TESTING = "true"
$env:DATABASE_URL = "sqlite:///:memory:"

# 1. Testes Unitários
Write-Host "📦 1/3 - Testes Unitários..." -ForegroundColor Cyan
python -m pytest tests/unit/ -v --tb=short --maxfail=5 -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Alguns testes unitários falharam, mas continuando..." -ForegroundColor Yellow
}

Write-Host ""

# 2. Testes de Integração
Write-Host "🔗 2/3 - Testes de Integração..." -ForegroundColor Cyan
python -m pytest tests/integration/ -v --tb=short --maxfail=5 -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Alguns testes de integração falharam, mas continuando..." -ForegroundColor Yellow
}

Write-Host ""

# 3. Testes de Automação
Write-Host "🤖 3/3 - Testes de Automação..." -ForegroundColor Cyan
python -m pytest tests/automation/ -v --tb=short -q

Write-Host ""
Write-Host "✅ Suite de testes concluída!" -ForegroundColor Green
