# Makefile para AgroKongo
# Comandos comuns para desenvolvimento, testes e deploy

.PHONY: help dev test lint clean seed db-migrate db-downgrade db-reset run-worker run-beat

# =============================================================================
# HELP
# =============================================================================

help: ## Mostra esta ajuda
	@echo "AgroKongo - Comandos Disponíveis"
	@echo "================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[92m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""


# =============================================================================
# DESENVOLVIMENTO
# =============================================================================

dev: ## Inicia servidor de desenvolvimento Flask
	@echo "🚀 Iniciando servidor de desenvolvimento..."
	python run.py

dev-debug: ## Inicia servidor com debug máximo
	@echo "🐛 Iniciando servidor com debug..."
	FLASK_ENV=development FLASK_DEBUG=1 python run.py

setup: ## Instala dependências e configura ambiente
	@echo "📦 Instalando dependências..."
	pip install -r requirements-dev.in
	pip install -r requirements-test.txt
	@echo "✅ Dependências instaladas!"
	@echo ""
	@echo "💡 Dica: Execute 'make seed' para popular o banco"


# =============================================================================
# TESTES
# =============================================================================

test: ## Executa todos os testes
	@echo "🧪 Executando testes..."
	pytest tests/ -v --tb=short

test-unit: ## Executa apenas testes unitários
	@echo "🧪 Executando testes unitários..."
	pytest tests/unit/ -v

test-integration: ## Executa testes de integração
	@echo "🧪 Executando testes de integração..."
	pytest tests/integration/ -v

test-cov: ## Executa testes com cobertura
	@echo "🧪 Executando testes com cobertura..."
	pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

test-framework: ## Executa testes do framework
	@echo "🧪 Executando testes do framework..."
	python -m pytest tests_framework/ -v

test-auth: ## Executa testes de autenticação
	@echo "🧪 Executando testes de auth..."
	python -m pytest tests_framework/test_auth_security.py -v

test-financial: ## Executa testes financeiros
	@echo "🧪 Executando testes financeiros..."
	python -m pytest tests_framework/test_financial_transactions.py -v


# =============================================================================
# QUALIDADE DE CÓDIGO
# =============================================================================

lint: ## Executa linter (flake8)
	@echo "🔍 Executando flake8..."
	flake8 app/ tests/ scripts/ --max-line-length=120 --exclude=migrations,archive,node_modules

format: ## Formata código (requere black)
	@echo "✨ Formatando código..."
	black app/ tests/ scripts/ --line-length 120

check-types: ## Verifica type hints (mypy)
	@echo "🔍 Verificando tipos..."
	mypy app/ --ignore-missing-imports


# =============================================================================
# BANCO DE DADOS
# =============================================================================

seed: ## Popula banco com dados de exemplo
	@echo "🌱 Executando seed..."
	python scripts/seed.py

db-migrate: ## Aplica migrações
	@echo "📊 Aplicando migrações..."
	flask db upgrade

db-downgrade: ## Reverte última migração
	@echo "📊 Revertendo migração..."
	flask db downgrade -1

db-migration MESSAGE ?= "migration": ## Cria nova migração (uso: make db-migration MESSAGE="add users")
	@echo "📝 Criando migração: $(MESSAGE)"
	flask db migrate -m "$(MESSAGE)"

db-reset: ## Reseta completamente o banco (DESTRUTIVO!)
	@echo "⚠️  ATENÇÃO: Isso apagará TODOS os dados do banco!"
	@read -p "Tem certeza? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	python scripts/resetar_banco.py
	@echo "✅ Banco resetado!"


# =============================================================================
# CELERY WORKER
# =============================================================================

run-worker: ## Inicia worker Celery
	@echo "👷 Iniciando worker Celery..."
	python celery_worker.py

run-beat: ## Inicia Celery Beat (agendador)
	@echo "⏰ Iniciando Celery Beat..."
	celery -A celery_worker beat --loglevel=INFO

run-worker-windows: ## Inicia worker no Windows
	@echo "👷 Iniciando worker Celery (Windows)..."
	python celery_worker.py

worker-shell: ## Abre shell Python com contexto da app
	@echo "🐍 Abrindo shell Python..."
	python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); print('Shell pronto! Use db.session para acessar o banco.')"


# =============================================================================
# LIMPEZA
# =============================================================================

clean: ## Limpa arquivos temporários
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf logs/*.log
	@echo "✅ Limpeza concluída!"

clean-all: clean ## Limpeza profunda (inclui node_modules)
	@echo "🧹 Limpeza profunda..."
	rm -rf node_modules/
	rm -rf frontend/.next/
	rm -rf frontend/node_modules/
	@echo "✅ Limpeza profunda concluída!"


# =============================================================================
# DOCKER
# =============================================================================

docker-up: ## Inicia containers Docker
	@echo "🐳 Iniciando Docker..."
	docker-compose up -d

docker-down: ## Para containers Docker
	@echo "🐳 Parando Docker..."
	docker-compose down

docker-logs: ## Mostra logs dos containers
	@echo "🐳 Logs dos containers..."
	docker-compose logs -f

docker-rebuild: ## Rebuild dos containers
	@echo "🐳 Rebuild dos containers..."
	docker-compose down
	docker-compose up -d --build


# =============================================================================
# UTILITÁRIOS
# =============================================================================

secret-key: ## Gera nova SECRET_KEY
	@echo "🔑 Gerando nova SECRET_KEY..."
	python gerar_secret_key.py

env-check: ## Verifica variáveis de ambiente
	@echo "🔍 Verificando variáveis de ambiente..."
	@if [ ! -f .env ]; then \
		echo "❌ .env não encontrado! Copie .env.example para .env"; \
		exit 1; \
	else \
		echo "✅ .env encontrado"; \
	fi

health: ## Executa health checks
	@echo "🏥 Executando health checks..."
	curl -f http://localhost:5000/health/live || echo "❌ App não respondendo"
	curl -f http://localhost:5000/health/ready || echo "❌ App não pronta"
	curl -f http://localhost:5000/health/db-ping || echo "❌ Database não respondendo"


# =============================================================================
# DEPLOY (LOCAL)
# =============================================================================

build-frontend: ## Build do frontend Next.js
	@echo "🏗️  Build do frontend..."
	cd frontend && npm install && npm run build

deploy-local: ## Deploy local completo
	@echo "🚀 Deploy local..."
	$(MAKE) db-migrate
	$(MAKE) seed
	$(MAKE) build-frontend
	@echo "✅ Deploy local concluído!"
