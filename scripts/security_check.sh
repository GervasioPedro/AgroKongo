#!/bin/bash

# --- Script de Verificação de Segurança ---
# Este script deve ser executado antes de cada commit ou deploy.

echo "🔍 Iniciando verificação de segurança..."

# 1. Verificar vulnerabilidades no código (Bandit)
echo "🛡️  Executando Bandit (Análise Estática de Segurança)..."
bandit -r app -c .flake8 -f txt

if [ $? -ne 0 ]; then
    echo "❌ Bandit encontrou problemas de segurança!"
    exit 1
fi

# 2. Verificar vulnerabilidades nas dependências (Safety)
echo "📦 Executando Safety (Verificação de Dependências)..."
safety check -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Safety encontrou vulnerabilidades nas dependências!"
    exit 1
fi

echo "✅ Verificação de segurança concluída com sucesso!"
exit 0
