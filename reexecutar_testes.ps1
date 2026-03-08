# Script para limpar cache Python e re-executar testes
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LIMPANDO CACHE E RE-EXECUTANDO TESTES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Limpar cache
Write-Host "1. Limpando cache do Python..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Include *.pyc -Recurse -Force | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "2. Executando testes de cadastro (API)..." -ForegroundColor Yellow
python -m pytest tests/integration/test_cadastro_flow.py::TestCadastroFlowAPI -v --tb=short > testes_api_result.txt 2>&1
Get-Content testes_api_result.txt

Write-Host ""
Write-Host "3. Executando testes de cadastro (Performance)..." -ForegroundColor Yellow
python -m pytest tests/integration/test_cadastro_flow.py::TestCadastroFlowPerformance -v --tb=short > testes_perf_result.txt 2>&1
Get-Content testes_perf_result.txt

Write-Host ""
Write-Host "4. Gerando novo arquivo de erros..." -ForegroundColor Yellow
python -m pytest tests/integration/ -v --tb=short > erros_novo.txt 2>&1
Write-Host "Novo arquivo 'erros_novo.txt' gerado!" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CONCLUÍDO!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
