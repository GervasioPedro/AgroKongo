#!/bin/bash
# Script para rodar todos os testes com relatório completo de coverage

echo "=========================================="
echo "  AgroKongo - Suite Completa de Testes"
echo "=========================================="
echo ""

# Instalar dependências de teste se necessário
echo "📦 Verificando dependências..."
pip install pytest-cov pytest-mock faker --quiet

echo ""
echo "🧪 Rodando testes unitários..."
echo "-------------------------------------------"
python -m pytest tests/unit/ -v \
    --cov=app/services \
    --cov=app/utils \
    --cov-report=term-missing \
    --tb=short

echo ""
echo "🔗 Rodando testes de integração..."
echo "-------------------------------------------"
python -m pytest tests/integration/ -v \
    --cov=app/routes \
    --cov=app/models \
    --cov-report=term-missing \
    --tb=short

echo ""
echo "🌐 Rodando testes de API e autenticação..."
echo "-------------------------------------------"
python -m pytest tests/test_*.py -v \
    --cov=app/__init__ \
    --cov-report=term-missing \
    --tb=short

echo ""
echo "📊 Gerando relatório HTML de cobertura..."
echo "-------------------------------------------"
python -m pytest tests/ \
    --cov=app \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --cov-report=term-summary

echo ""
echo "✅ Relatório HTML disponível em: htmlcov/index.html"
echo ""
echo "📈 Resumo da Cobertura:"
echo "-------------------------------------------"
# Extrair apenas o resumo final
python -m pytest tests/ --cov=app --cov-report=term-summary | tail -20

echo ""
echo "=========================================="
echo "  Todos os testes concluídos!"
echo "=========================================="
