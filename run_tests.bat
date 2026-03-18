@echo off
REM Script para rodar testes rapidamente no Windows
REM Sem caracteres especiais para evitar problemas de encoding

echo ============================================
echo   AgroKongo - Test Runner (Windows)
echo ============================================
echo.

echo Executando testes unitarios...
python -m pytest tests/unit/ -v --tb=short

echo.
echo Executando testes de integracao...
python -m pytest tests/integration/ -v --tb=short

echo.
echo Executando todos os testes...
python -m pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

echo.
echo ============================================
echo   Todos os testes concluidos!
echo ============================================
