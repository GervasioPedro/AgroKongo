# Executar Testes Específicos do AgroKongo

Write-Host "🚀 Executando testes específicos..." -ForegroundColor Green
Write-Host ""

# 1. Testes de Criptografia (Segurança)
Write-Host "🔐 Testes de Criptografia..." -ForegroundColor Cyan
python -m pytest tests/unit/test_criptografia.py -v --tb=short

Write-Host ""

# 2. Testes Financeiros (Críticos)
Write-Host "💰 Testes Financeiros..." -ForegroundColor Cyan
python -m pytest tests/unit/test_financeiro.py -v --tb=short

Write-Host ""

# 3. Testes de Decorators e Tasks
Write-Host "⚙️  Testes de Decorators e Tasks..." -ForegroundColor Cyan
python -m pytest tests/unit/test_decorators_tasks.py -v --tb=short

Write-Host ""

# 4. Testes de Helpers e Utils
Write-Host "🔧 Testes de Helpers e Utils..." -ForegroundColor Cyan
python -m pytest tests/unit/test_helpers.py tests/unit/test_utils.py -v --tb=short

Write-Host ""

Write-Host "✅ Testes específicos concluídos!" -ForegroundColor Green
