#!/bin/bash
# run_tests.sh - Script para executar suíte de testes do AgroKongo
# Execução organizada de testes unitários, integração e cobertura

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

# Criar ambiente virtual para testes se não existir
if [ ! -d "venv-test" ]; then
    print_status "Criando ambiente virtual para testes..."
    python -m venv venv-test
fi

# Ativar ambiente virtual
source venv-test/bin/activate

# Instalar dependências de teste
print_status "Instalando dependências de teste..."
pip install -r requirements-test.txt

# Exportar variáveis de ambiente para testes
export FLASK_ENV=testing
export TESTING=True
export SQLALCHEMY_DATABASE_URI=sqlite:///test.db
export CELERY_BROKER_URL=memory://
export CELERY_RESULT_BACKEND=memory://

# Limpar banco de testes anterior
if [ -f "test.db" ]; then
    rm test.db
    print_status "Banco de testes anterior removido"
fi

# Executar testes unitários
print_status "Executando testes unitários..."
echo "=========================================="

# Testes de modelos
print_status "Testando modelos..."
pytest tests/unit/test_models.py -v --tb=short

# Testes de utilitários
print_status "Testando utilitários de negócio..."
pytest tests/unit/test_utils.py -v --tb=short

# Testes de gestão de stock
print_status "Testando gestão de stock..."
pytest tests/unit/test_stock.py -v --tb=short

# Testes financeiros
print_status "Testando cálculos financeiros..."
pytest tests/unit/test_financeiro.py -v --tb=short

echo "=========================================="
print_success "Testes unitários concluídos!"

# Gerar relatório de cobertura
print_status "Gerando relatório de cobertura..."
pytest tests/unit/ --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Verificar cobertura
if [ $? -eq 0 ]; then
    print_success "Cobertura de testes adequada (>80%)"
else
    print_warning "Cobertura de testes abaixo do esperado (<80%)"
fi

# Executar testes de performance (opcional)
if command -v pytest-benchmark &> /dev/null; then
    print_status "Executando testes de performance..."
    pytest tests/unit/test_financeiro.py::TestCalculosFinanceiros::test_calculo_comissao_plataforma_10_porcento --benchmark-only
fi

# Gerar relatório HTML dos testes
print_status "Gerando relatório HTML dos testes..."
pytest tests/unit/ --html=reports/test_report.html --self-contained-html

# Resumo dos resultados
echo "=========================================="
print_status "RESUMO DOS TESTES"
echo "=========================================="
echo "• Testes unitários: Concluídos"
echo "• Cobertura: Verificar em htmlcov/index.html"
echo "• Relatório HTML: reports/test_report.html"
echo "• Banco de testes: test.db (removido após uso)"

# Limpeza
print_status "Limpando ambiente..."
rm -f test.db

print_success "Todos os testes executados com sucesso!"

# Instruções para próximos passos
echo ""
echo "Próximos passos:"
echo "1. Verifique o relatório de cobertura: htmlcov/index.html"
echo "2. Analise o relatório detalhado: reports/test_report.html"
echo "3. Execute testes de integração quando disponível"
echo "4. Configure CI/CD para execução automática"

# Desativar ambiente virtual
deactivate
