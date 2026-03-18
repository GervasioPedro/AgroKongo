# Makefile para AgroKongo - Automação de Tarefas de Desenvolvimento

.PHONY: help dev prod test clean logs

# Variáveis
DOCKER_COMPOSE = docker-compose
PYTHON = python3
PIP = pip3

help: ## Mostra esta ajuda
	@echo "AgroKongo - Comandos Disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

dev: ## Inicia ambiente de desenvolvimento com Docker
	$(DOCKER_COMPOSE) up -d db redis
	@echo "Aguardando banco de dados..."
	@sleep 5
	$(DOCKER_COMPOSE) up -d web celery_worker celery_beat
	@echo "✅ AgroKongo iniciado em http://localhost:5000"

prod: ## Inicia ambiente de produção
	$(DOCKER_COMPOSE) -f docker-compose.yml up -d
	@echo "✅ Produção iniciada"

stop: ## Para todos os serviços
	$(DOCKER_COMPOSE) down

restart: stop dev ## Reinicia todos os serviços

logs: ## Mostra logs em tempo real
	$(DOCKER_COMPOSE) logs -f

logs-web: ## Logs apenas do web
	$(DOCKER_COMPOSE) logs -f web

logs-celery: ## Logs apenas do celery
	$(DOCKER_COMPOSE) logs -f celery_worker

db-migrate: ## Executa migrações do banco de dados
	$(DOCKER_COMPOSE) exec web flask db migrate
	$(DOCKER_COMPOSE) exec web flask db upgrade

db-upgrade: ## Aplica migrações pendentes
	$(DOCKER_COMPOSE) exec web flask db upgrade

db-downgrade: ## Reverte última migração
	$(DOCKER_COMPOSE) exec web flask db downgrade -1

db-seed: ## Popula banco com dados de teste
	$(DOCKER_COMPOSE) exec web python seed.py

test: ## Roda todos os testes
	$(PYTHON) -m pytest tests/ -v --cov=app --cov-report=html

test-unit: ## Roda apenas testes unitários
	$(PYTHON) -m pytest tests/unit/ -v

test-integration: ## Roda apenas testes de integração
	$(PYTHON) -m pytest tests/integration/ -v

test-coverage: ## Gera relatório de cobertura de testes
	$(PYTHON) -m pytest tests/ --cov=app --cov-report=html
	@echo "✅ Relatório gerado em htmlcov/index.html"

shell: ## Abre shell Python no container web
	$(DOCKER_COMPOSE) exec web flask shell

db-shell: ## Abre shell SQL no banco de dados
	$(DOCKER_COMPOSE) exec db psql -U agrokongo -d agrokongo

redis-cli: ## Conecta ao Redis CLI
	$(DOCKER_COMPOSE) exec redis redis-cli

clean: ## Limpa arquivos temporários e caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	rm -rf instance/*.db
	@echo "✅ Limpeza concluída"

setup: ## Instala dependências e configura ambiente
	$(PIP) install -r requirements.txt
	cp .env.example .env 2>/dev/null || true
	@echo "✅ Setup concluído. Edite o arquivo .env com suas configurações."

celery-flower: ## Inicia Flower para monitoramento Celery
	$(DOCKER_COMPOSE) exec celery_worker celery flower --port=5555

backup-db: ## Faz backup do banco de dados
	@echo "Criando backup..."
	@mkdir -p backups
	@docker exec $$(docker-compose ps -q db) pg_dump -U agrokongo agrokongo > backups/agrokongo_$$(date +%Y%m%d_%H%M%S).sql
	@echo "✅ Backup criado em backups/"

restore-db: ## Restaura banco de dados a partir de backup
	@echo "Use: make restore-db FILE=backups/agrokongo_YYYYMMDD_HHMMSS.sql"
	@if [ -z "$(FILE)" ]; then echo "Erro: Especifique FILE="; exit 1; fi
	docker exec -i $$(docker-compose ps -q db) psql -U agrokongo -d agrokongo < $(FILE)
	@echo "✅ Banco restaurado"

health: ## Verifica saúde de todos os serviços
	@echo "Verificando saúde dos serviços..."
	@curl -f http://localhost:5000/health || echo "❌ Web não respondendo"
	@docker exec $$(docker-compose ps -q db) pg_isready -U agrokongo || echo "❌ DB não respondendo"
	@docker exec $$(docker-compose ps -q redis) redis-cli ping || echo "❌ Redis não respondendo"
	@echo ""

stats: ## Mostra estatísticas do sistema
	@echo "=== Estatísticas AgroKongo ==="
	@docker stats --no-stream
	@echo ""
	@docker-compose ps
