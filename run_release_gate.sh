#!/bin/bash
# run_release_gate.sh - Script completo para Release Gate
# Executa todas as verificações de pré-lançamento

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Função para imprimir mensagens
print_header() {
    echo -e "\n${CYAN}=================================================="
    echo -e "$1"
    echo -e "==================================================${NC}"
}

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

print_header "🚀 AGROKONGO - RELEASE GATE AUTOMATIZADO"
print_status "Verificação Final de Pré-Lançamento"
print_status "Data: $(date '+%d/%m/%Y %H:%M:%S')"

# Criar ambiente virtual se não existir
if [ ! -d "venv-release" ]; then
    print_status "Criando ambiente virtual para release..."
    python -m venv venv-release
fi

# Ativar ambiente virtual
source venv-release/bin/activate

# Instalar dependências
print_status "Instalando dependências..."
pip install -r requirements.txt
pip install -r requirements-test.txt

# Instalar ferramentas de segurança
pip install bandit[toml] safety trufflehog pip-audit flake8 pytest-cov

echo ""
print_header "📋 VERIFICAÇÃO 1: COBERTURA DE TESTES > 80%"
echo "--------------------------------------------------"

print_status "Executando testes com cobertura..."

if python -m pytest tests/ --cov=app --cov-report=json --cov-report=term-missing --cov-fail-under=80; then
    # Extrair cobertura
    COVERAGE=$(python -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")")
    print_success "✅ Cobertura de testes: ${COVERAGE}% (>80%)"
    COVERAGE_PASSED=true
else
    print_error "❌ Cobertura de testes abaixo de 80%"
    COVERAGE_PASSED=false
fi

echo ""
print_header "🔒 VERIFICAÇÃO 2: ZERO VULNERABILIDADES ALTAS"
echo "----------------------------------------------------"

print_status "Executando scan de segurança completo..."

if python security_scan.py; then
    print_success "✅ Scan de segurança: Zero vulnerabilidades altas"
    SECURITY_PASSED=true
else
    print_error "❌ Scan de segurança: Vulnerabilidades altas encontradas"
    SECURITY_PASSED=false
fi

echo ""
print_header "💰 VERIFICAÇÃO 3: PEER REVIEW FINANCEIRO"
echo "------------------------------------------------"

print_status "Executando validação de fluxos financeiros..."

if python -m pytest tests/integration/test_fim_de_ciclo.py::TestValidacoesFinanceiras -v; then
    print_success "✅ Peer review financeiro: Fluxos validados"
    FINANCIAL_PASSED=true
else
    print_error "❌ Peer review financeiro: Problemas encontrados"
    FINANCIAL_PASSED=false
fi

echo ""
print_header "🔄 VERIFICAÇÃO 4: TESTE FIM DE CICLO"
echo "--------------------------------------------"

print_status "Executando teste E2E completo..."

if python -m pytest tests/integration/test_fim_de_ciclo.py::TestFimDeCicloCompleto::test_ciclo_completo_sucesso -v -s; then
    print_success "✅ Teste E2E: Ciclo completo validado"
    E2E_PASSED=true
else
    print_error "❌ Teste E2E: Falha no ciclo completo"
    E2E_PASSED=false
fi

echo ""
print_header "🗄️ VERIFICAÇÃO 5: DATABASE MIGRATIONS"
echo "-----------------------------------------"

print_status "Verificando migrations necessárias..."

if [ -f "migrations/versions/implementar_status_conta_carteiras.py" ]; then
    print_success "✅ Database migrations: Migration status_conta presente"
    MIGRATIONS_PASSED=true
else
    print_error "❌ Database migrations: Migration status_conta ausente"
    MIGRATIONS_PASSED=false
fi

echo ""
print_header "⚙️ VERIFICAÇÃO 6: CONFIGURAÇÃO"
echo "----------------------------------"

print_status "Verificando arquivos de configuração..."

CONFIG_FILES=("app/__init__.py" "app/models.py" "app/models_carteiras.py" "app/services/otp_service.py" "requirements.txt")
CONFIG_MISSING=0

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "✅ $file presente"
    else
        print_error "❌ $file ausente"
        CONFIG_MISSING=$((CONFIG_MISSING + 1))
    fi
done

if [ $CONFIG_MISSING -eq 0 ]; then
    CONFIG_PASSED=true
else
    CONFIG_PASSED=false
fi

echo ""
print_header "🔍 VERIFICAÇÃO 7: QUALIDADE DE CÓDIGO"
echo "----------------------------------------"

print_status "Verificando qualidade com Flake8..."

if flake8 app/ --max-line-length=120 --ignore=E203,W503 --count --statistics; then
    print_success "✅ Código dentro dos padrões de qualidade"
    QUALITY_PASSED=true
else
    print_warning "⚠️ Problemas de qualidade encontrados (não críticos)"
    QUALITY_PASSED=true  # Não bloqueante
fi

echo ""
print_header "📚 VERIFICAÇÃO 8: DOCUMENTAÇÃO"
echo "------------------------------------"

print_status "Verificando documentação..."

DOC_FILES=("README.md" "tests/README.md")
DOC_MISSING=0

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "✅ $file presente"
    else
        print_error "❌ $file ausente"
        DOC_MISSING=$((DOC_MISSING + 1))
    fi
done

if [ $DOC_MISSING -eq 0 ]; then
    DOCS_PASSED=true
else
    DOCS_PASSED=false
fi

echo ""
print_header "📊 RESUMO DO RELEASE GATE"
echo "==========================="

# Contadores
TOTAL_CHECKS=8
PASSED_CHECKS=0
FAILED_CHECKS=0

# Verificar status
[ "$COVERAGE_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))
[ "$SECURITY_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))
[ "$FINANCIAL_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))
[ "$E2E_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))
[ "$MIGRATIONS_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))
[ "$CONFIG_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))
[ "$QUALITY_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))
[ "$DOCS_PASSED" = true ] && PASSED_CHECKS=$((PASSED_CHECKS + 1)) || FAILED_CHECKS=$((FAILED_CHECKS + 1))

echo "📋 Total de verificações: $TOTAL_CHECKS"
echo "✅ Verificações passadas: $PASSED_CHECKS"
echo "❌ Verificações falhadas: $FAILED_CHECKS"
echo "📊 Cobertura de testes: ${COVERAGE:-0}%"

echo ""
echo "🎯 STATUS DAS VERIFICAÇÕES:"
echo "   [${COVERAGE_PASSED:+✅}${COVERAGE_PASSED:-❌}] Cobertura de Testes > 80%"
echo "   [${SECURITY_PASSED:+✅}${SECURITY_PASSED:-❌}] Zero Vulnerabilidades Altas"
echo "   [${FINANCIAL_PASSED:+✅}${FINANCIAL_PASSED:-❌}] Peer Review Financeiro"
echo "   [${E2E_PASSED:+✅}${E2E_PASSED:-❌}] Teste Fim de Ciclo"
echo "   [${MIGRATIONS_PASSED:+✅}${MIGRATIONS_PASSED:-❌}] Database Migrations"
echo "   [${CONFIG_PASSED:+✅}${CONFIG_PASSED:-❌}] Configuração"
echo "   [${QUALITY_PASSED:+✅}${QUALITY_PASSED:-❌}] Qualidade de Código"
echo "   [${DOCS_PASSED:+✅}${DOCS_PASSED:-❌}] Documentação"

echo ""
echo "🚨 CRITÉRIOS OBRIGATÓRIOS:"
CRITICAL_PASSED=true

[ "$COVERAGE_PASSED" = true ] && echo "   ✅ Cobertura > 80%" || { echo "   ❌ Cobertura > 80%"; CRITICAL_PASSED=false; }
[ "$SECURITY_PASSED" = true ] && echo "   ✅ Zero Vulnerabilidades Altas" || { echo "   ❌ Zero Vulnerabilidades Altas"; CRITICAL_PASSED=false; }
[ "$FINANCIAL_PASSED" = true ] && echo "   ✅ Peer Review Financeiro" || { echo "   ❌ Peer Review Financeiro"; CRITICAL_PASSED=false; }
[ "$E2E_PASSED" = true ] && echo "   ✅ Teste Fim de Ciclo" || { echo "   ❌ Teste Fim de Ciclo"; CRITICAL_PASSED=false; }

echo ""
print_header "🎉 DECISÃO FINAL"

if [ "$CRITICAL_PASSED" = true ]; then
    print_success "🚀 RELEASE APROVADO!"
    echo "✅ Todos os critérios obrigatórios foram atendidos"
    echo "✅ Sistema pronto para produção"
    
    echo ""
    echo "📄 RELATÓRIOS GERADOS:"
    echo "   • coverage.json - Detalhes da cobertura"
    echo "   • security_summary.json - Scan de segurança"
    echo "   • release_gate_report.json - Resumo completo"
    
    echo ""
    echo "🔗 PRÓXIMOS PASSOS:"
    echo "   1. Review dos relatórios gerados"
    echo "   2. Deploy para ambiente de staging"
    echo "   3. Testes finais em staging"
    echo "   4. Deploy para produção"
    echo "   5. Monitoramento pós-lançamento"
    
    echo ""
    print_success "🌱 AgroKongo pronto para lançamento!"
    
    exit 0
else
    print_error "🚫 RELEASE BLOQUEADO!"
    echo "❌ Critérios obrigatórios não atendidos"
    
    echo ""
    echo "🔧 AÇÕES NECESSÁRIAS:"
    [ "$COVERAGE_PASSED" = false ] && echo "   • Aumentar cobertura de testes para >80%"
    [ "$SECURITY_PASSED" = false ] && echo "   • Corrigir vulnerabilidades de segurança"
    [ "$FINANCIAL_PASSED" = false ] && echo "   • Corrigir problemas nos fluxos financeiros"
    [ "$E2E_PASSED" = false ] && echo "   • Corrigir falha no teste E2E"
    
    echo ""
    echo "📋 VERIFICAÇÕES BLOQUEANTES:"
    [ "$COVERAGE_PASSED" = false ] && echo "   ❌ Cobertura de Testes > 80%"
    [ "$SECURITY_PASSED" = false ] && echo "   ❌ Zero Vulnerabilidades Altas"
    [ "$FINANCIAL_PASSED" = false ] && echo "   ❌ Peer Review Financeiro"
    [ "$E2E_PASSED" = false ] && echo "   ❌ Teste Fim de Ciclo"
    
    exit 1
fi
