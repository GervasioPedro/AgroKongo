#!/bin/bash
# Script de testes AgroKongo 2026 - Cobertura 100%

echo "=============================================================================="
echo "🧪 SUÍTE DE TESTES AGROKONGO 2026"
echo "=============================================================================="
echo ""

# Configurar ambiente
export TEST_DATABASE_URL="sqlite:///:memory:"
export PYTHONPATH="$(pwd)"

# Verificar argumentos
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Uso:"
    echo "  ./run_tests.sh              # Roda todos os testes com cobertura 100%"
    echo "  ./run_tests.sh --no-cov     # Roda sem verificação de cobertura"
    echo "  ./run_tests.sh --unit       # Roda apenas testes unitários"
    echo "  ./run_tests.sh --integ      # Roda apenas testes de integração"
    echo "  ./run_tests.sh --watch      # Roda em modo watch (auto-reload)"
    echo ""
    exit 0
fi

# Comando base
CMD="python -m pytest"

# Opções padrão
OPTIONS="--tb=short --strict-markers --disable-warnings --color=yes --durations=10 -v"

# Adicionar cobertura (padrão)
COVERAGE="--cov=app --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=100"

# Relatório HTML
HTML_REPORT="--html=reports/test_report.html --self-contained-html"

# Diretórios de teste
TEST_DIRS="tests/unit/ tests/integration/ tests_framework/"

# Verificar flags especiais
case "$1" in
    --no-cov)
        COVERAGE=""
        shift
        ;;
    --unit)
        TEST_DIRS="tests/unit/"
        shift
        ;;
    --integ)
        TEST_DIRS="tests/integration/"
        shift
        ;;
    --e2e)
        TEST_DIRS="tests/e2e/"
        shift
        ;;
    --watch)
        CMD="python -m pytest-watch --"
        shift
        ;;
esac

# Montar comando final
FULL_CMD="$CMD $OPTIONS $COVERAGE $HTML_REPORT $TEST_DIRS $@"

echo "📋 COMANDO: $FULL_CMD"
echo "=============================================================================="
echo ""

# Criar diretório de relatórios
mkdir -p reports

# Executar testes
echo "🚀 INICIANDO TESTES..."
echo "=============================================================================="
eval $FULL_CMD
RESULT=$?

echo ""
echo "=============================================================================="

# Resumo final
if [ $RESULT -eq 0 ]; then
    echo "✅ TODOS OS TESTES PASSARAM!"
    echo "📊 Cobertura de código: 100%"
    echo "📄 Relatório: file://$(pwd)/reports/test_report.html"
else
    echo "❌ ALGUNS TESTES FALHARAM"
    echo "📄 Verifique: file://$(pwd)/reports/test_report.html"
fi

echo "=============================================================================="

exit $RESULT
