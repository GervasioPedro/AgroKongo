@echo off
REM Executar validação de tabelas e testes
python tests_framework\validate_tables.py
if errorlevel 1 (
    echo ERRO na criacao das tabelas!
    exit /b 1
)

echo.
echo ========================================
echo TABELAS VALIDADAS - EXECUTANDO TESTES
echo ========================================
echo.

python -m pytest tests_framework/ -v --tb=short --maxfail=5
pause
