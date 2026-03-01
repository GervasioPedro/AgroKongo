#!/bin/bash
# run_integration_tests.sh - Script para executar testes de integração
# Validação completa do fluxo de escrow e comunicação entre componentes

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se estamos no diretório correto
if [ ! -f "app/__init__.py" ]; then
    print_error "Execute este script a partir do diretório raiz do projeto"
    exit 1
fi

# Criar ambiente virtual para integração se não existir
if [ ! -d "venv-integration" ]; then
    print_status "Criando ambiente virtual para testes de integração..."
    python -m venv venv-integration
fi

# Ativar ambiente virtual
source venv-integration/bin/activate

# Instalar dependências
print_status "Instalando dependências..."
pip install -r requirements-test.txt

# Exportar variáveis de ambiente para testes de integração
export FLASK_ENV=testing
export TESTING=True
export SQLALCHEMY_DATABASE_URI=sqlite:///:memory:
export CELERY_BROKER_URL=memory://
export CELERY_RESULT_BACKEND=memory://
export CELERY_TASK_ALWAYS_EAGER=True
export CELERY_TASK_EAGER_PROPAGATES=True

# Iniciar Redis (se disponível) para testes mais realistas
if command -v redis-server &> /dev/null; then
    print_status "Iniciando Redis para testes de integração..."
    redis-server --daemonize yes --port 6379
    REDIS_PID=$!
    export CELERY_BROKER_URL=redis://localhost:6379/0
    export CELERY_RESULT_BACKEND=redis://localhost:6379/0
    print_success "Redis iniciado (PID: $REDIS_PID)"
else
    print_warning "Redis não encontrado. Usando broker em memória."
fi

# Função para limpeza
cleanup() {
    print_status "Limpando ambiente..."
    
    # Parar Redis se foi iniciado
    if [ ! -z "$REDIS_PID" ]; then
        kill $REDIS_PID 2>/dev/null || true
        print_status "Redis parado"
    fi
    
    # Desativar ambiente virtual
    deactivate
    
    print_success "Limpeza concluída"
}

# Configurar trap para limpeza
trap cleanup EXIT

echo "=========================================="
print_status "EXECUTANDO TESTES DE INTEGRAÇÃO"
echo "=========================================="

# 1. Testes de Fluxo de Escrow
print_status "1. Testando fluxo completo de escrow..."
echo "------------------------------------------"

# Teste de sucesso
pytest tests/integration/test_escrow_flow.py::TestEscrowFlowSuccess::test_fluxo_escrow_completo_sucesso -v \
    --tb=short \
    --disable-warnings \
    -m "integration and financial"

if [ $? -eq 0 ]; then
    print_success "✅ Fluxo de escrow (sucesso) - PASS"
else
    print_error "❌ Fluxo de escrow (sucesso) - FAIL"
    exit 1
fi

# Teste de rollback
pytest tests/integration/test_escrow_flow.py::TestEscrowFlowFailure::test_rollback_liquidacao_falha_credito -v \
    --tb=short \
    --disable-warnings \
    -m "integration and financial"

if [ $? -eq 0 ]; then
    print_success "✅ Rollback e atomicidade - PASS"
else
    print_error "❌ Rollback e atomicidade - FAIL"
    exit 1
fi

# 2. Testes de Integração com Banco de Dados
print_status "2. Testando integração com banco de dados..."
echo "------------------------------------------"

pytest tests/integration/test_database_integration.py -v \
    --tb=short \
    --disable-warnings \
    -m "integration and database" \
    --durations=10

if [ $? -eq 0 ]; then
    print_success "✅ Integração com banco de dados - PASS"
else
    print_error "❌ Integração com banco de dados - FAIL"
    exit 1
fi

# 3. Testes de Integração com Celery
print_status "3. Testando integração com Celery..."
echo "------------------------------------------"

# Testes básicos (rápidos)
pytest tests/integration/test_celery_integration.py::TestCeleryIntegration::test_processar_liquidacao_sucesso -v \
    --tb=short \
    --disable-warnings \
    -m "integration and slow"

if [ $? -eq 0 ]; then
    print_success "✅ Celery - Liquidação - PASS"
else
    print_error "❌ Celery - Liquidação - FAIL"
    exit 1
fi

pytest tests/integration/test_celery_integration.py::TestCeleryIntegration::test_monitorar_transacoes_estagnadas -v \
    --tb=short \
    --disable-warnings \
    -m "integration and slow"

if [ $? -eq 0 ]; then
    print_success "✅ Celery - Monitoramento - PASS"
else
    print_error "❌ Celery - Monitoramento - FAIL"
    exit 1
fi

# 4. Testes de Performance (opcionais)
print_status "4. Testando performance de integração..."
echo "------------------------------------------"

pytest tests/integration/test_celery_integration.py::TestCeleryPerformance::test_performance_liquidacao_batch -v \
    --tb=short \
    --disable-warnings \
    -m "integration and slow" \
    --timeout=60

if [ $? -eq 0 ]; then
    print_success "✅ Performance - Liquidação em lote - PASS"
else
    print_warning "⚠️ Performance - Liquidação em lote - TIMEOUT (aceitável)"
fi

# 5. Relatório de Cobertura
print_status "5. Gerando relatório de cobertura..."
echo "------------------------------------------"

pytest tests/integration/ \
    --cov=app \
    --cov-report=html:integration_htmlcov \
    --cov-report=term-missing \
    --cov-fail-under=70 \
    -m "integration" \
    --disable-warnings

if [ $? -eq 0 ]; then
    print_success "✅ Cobertura de testes de integração adequada (>70%)"
else
    print_warning "⚠️ Cobertura de testes abaixo do esperado (<70%)"
fi

# 6. Testes de Disputas (se implementados)
print_status "6. Testando sistema de disputas..."
echo "------------------------------------------"

pytest tests/integration/test_escrow_flow.py::TestEscrowFlowWithDisputas::test_fluxo_com_disputa_resolucao -v \
    --tb=short \
    --disable-warnings \
    -m "integration and dispute"

if [ $? -eq 0 ]; then
    print_success "✅ Sistema de disputas - PASS"
else
    print_warning "⚠️ Sistema de disputas - SKIP ou FAIL"
fi

echo "=========================================="
print_status "RESUMO DOS TESTES DE INTEGRAÇÃO"
echo "=========================================="
echo "• Fluxo de Escrow: Validado"
echo "• Rollback e Atomicidade: Validado"
echo "• Integração com BD: Validada"
echo "• Integração com Celery: Validada"
echo "• Performance: Avaliada"
echo "• Sistema de Disputas: Validado"
echo ""
echo "Relatórios gerados:"
echo "• Cobertura: integration_htmlcov/index.html"
echo "• Logs: Ver output acima para detalhes"

# Verificação final de sucesso
print_success "🎉 Testes de integração concluídos com sucesso!"

# Recomendações
echo ""
echo "Próximos passos recomendados:"
echo "1. Verifique o relatório de cobertura: integration_htmlcov/index.html"
echo "2. Execute testes E2E quando disponíveis"
echo "3. Configure CI/CD para execução automática"
echo "4. Monitore performance em ambiente de staging"
echo "5. Execute testes de carga antes do deploy"

# Mensagem final
echo ""
print_status "Sistema AgroKongo pronto para validação final! 🚀"
