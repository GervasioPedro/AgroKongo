#!/bin/bash

# 🚀 Script de Deploy Automatizado - AgroKongo
# Este script prepara e faz deploy do projeto para produção

set -e  # Para em caso de erro

echo "🚜 AgroKongo - Deploy para Produção"
echo "===================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Verificar dependências
echo -e "${YELLOW}[1/6] Verificando dependências...${NC}"

if ! command_exists git; then
    echo -e "${RED}❌ Git não encontrado. Instale o Git primeiro.${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}❌ Python3 não encontrado. Instale o Python 3.11+${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ NPM não encontrado. Instale o Node.js primeiro.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Todas as dependências encontradas${NC}"
echo ""

# 2. Verificar variáveis de ambiente
echo -e "${YELLOW}[2/6] Verificando variáveis de ambiente...${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}❌ Ficheiro .env não encontrado!${NC}"
    echo "Crie um ficheiro .env com as seguintes variáveis:"
    echo "  - SECRET_KEY"
    echo "  - DATABASE_URL"
    echo "  - REDIS_URL"
    exit 1
fi

echo -e "${GREEN}✅ Ficheiro .env encontrado${NC}"
echo ""

# 3. Testar Backend
echo -e "${YELLOW}[3/6] Testando backend...${NC}"

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate || source venv/Scripts/activate

# Instalar dependências
pip install -r requirements.txt --quiet

# Executar testes
echo "Executando testes..."
python -m pytest tests/ -v --tb=short || {
    echo -e "${RED}❌ Testes falharam! Corrija os erros antes de fazer deploy.${NC}"
    exit 1
}

echo -e "${GREEN}✅ Backend testado com sucesso${NC}"
echo ""

# 4. Build do Frontend
echo -e "${YELLOW}[4/6] Building frontend...${NC}"

cd frontend

# Instalar dependências
npm install --silent

# Build
npm run build || {
    echo -e "${RED}❌ Build do frontend falhou!${NC}"
    exit 1
}

cd ..

echo -e "${GREEN}✅ Frontend compilado com sucesso${NC}"
echo ""

# 5. Commit e Push
echo -e "${YELLOW}[5/6] Fazendo commit das alterações...${NC}"

git add .
git commit -m "Deploy: $(date +'%Y-%m-%d %H:%M:%S')" || echo "Nada para commitar"
git push origin main

echo -e "${GREEN}✅ Código enviado para GitHub${NC}"
echo ""

# 6. Deploy
echo -e "${YELLOW}[6/6] Iniciando deploy...${NC}"

# Deploy do Frontend (Netlify)
if command_exists netlify; then
    echo "Fazendo deploy do frontend no Netlify..."
    cd frontend
    netlify deploy --prod --dir=.next
    cd ..
    echo -e "${GREEN}✅ Frontend deployed no Netlify${NC}"
else
    echo -e "${YELLOW}⚠️  Netlify CLI não encontrado. Deploy manual necessário.${NC}"
    echo "   Instale com: npm install -g netlify-cli"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deploy concluído com sucesso!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📝 Próximos passos:"
echo "  1. Verificar deploy no Netlify: https://app.netlify.com"
echo "  2. Verificar backend no Render: https://dashboard.render.com"
echo "  3. Testar aplicação em produção"
echo "  4. Monitorizar logs para erros"
echo ""
echo "🔗 URLs:"
echo "  Frontend: https://agrokongo.netlify.app"
echo "  Backend:  https://agrokongo-api.onrender.com"
echo "  Health:   https://agrokongo-api.onrender.com/health"
echo ""
