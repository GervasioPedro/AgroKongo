# 🚀 COMANDOS RÁPIDOS - AGROKONGO

Guia rápido de comandos para desenvolvimento, testes e operações diárias.

## 📋 Índice

- [Setup Inicial](#setup-inicial)
- [Desenvolvimento](#desenvolvimento)
- [Testes](#testes)
- [Banco de Dados](#banco-de-dados)
- [Celery Workers](#celery-workers)
- [Docker](#docker)
- [Utilitários](#utilitários)
- [Health Checks](#health-checks)

---

## 🛠️ Setup Inicial

### Primeira vez
```bash
# Instalar dependências
make setup

# Configurar variáveis de ambiente
cp .env.example .env

# Aplicar migrações
make db-migrate

# Popular banco com dados de exemplo
make seed

# Iniciar servidor de desenvolvimento
make dev
```

### Verificar ambiente
```bash
make env-check
```

---

## 💻 Desenvolvimento

### Servidor de desenvolvimento
```bash
# Modo normal
make dev

# Com debug máximo
make dev-debug
```

### Limpeza de código
```bash
# Executar linter
make lint

# Formatar código (requere black)
make format

# Verificar type hints
make check-types
```

---

## 🧪 Testes

### Executar todos os testes
```bash
make test
```

### Testes específicos
```bash
# Testes unitários
make test-unit

# Testes de integração
make test-integration

# Testes do framework
make test-framework

# Testes de autenticação
make test-auth

# Testes financeiros
make test-financial
```

### Com cobertura
```bash
make test-cov
```

---

## 🗄️ Banco de Dados

### Migrações
```bash
# Aplicar migrações
make db-migrate

# Reverter última migração
make db-downgrade

# Criar nova migração
make db-migration MESSAGE="descricao_da_migracao"

# Resetar banco (DESTRUTIVO!)
make db-reset
```

### Seed data
```bash
# Popular banco com dados de exemplo
make seed
```

---

## 👷 Celery Workers

### Worker padrão
```bash
make run-worker
```

### Windows
```bash
make run-worker-windows
```

### Agendador (Beat)
```bash
make run-beat
```

### Shell Python com contexto
```bash
make worker-shell
```

---

## 🐳 Docker

### Containers
```bash
# Iniciar containers
make docker-up

# Parar containers
make docker-down

# Ver logs
make docker-logs

# Rebuild
make docker-rebuild
```

---

## 🔧 Utilitários

### Gerar SECRET_KEY
```bash
make secret-key
```

### Health checks manuais
```bash
make health
```

### Limpeza
```bash
# Limpeza básica
make clean

# Limpeza profunda (inclui node_modules)
make clean-all
```

---

## 🏥 Health Checks

### Endpoints disponíveis

Após iniciar o servidor (`make dev`), acesse:

#### Liveness Probe
```bash
curl http://localhost:5000/health/live
```
Verifica se a aplicação está viva.

#### Readiness Probe
```bash
curl http://localhost:5000/health/ready
```
Verifica se a aplicação está pronta (DB, Redis, Storage).

#### Database Ping
```bash
curl http://localhost:5000/health/db-ping
```
Verifica conectividade com banco de dados.

#### Cache Ping
```bash
curl http://localhost:5000/health/cache-ping
```
Verifica conectividade com Redis/Cache.

#### Health Detalhado
```bash
curl http://localhost:5000/health/detailed
```
Métricas completas da aplicação.

---

## 📊 Credenciais de Teste (após `make seed`)

### Administrador
- **Email:** admin@agrokongo.ao
- **Senha:** Admin123!

### Produtor
- **Email:** joao.silva@example.ao
- **Senha:** Produtor123!

### Comprador
- **Email:** maria.santos@example.ao
- **Senha:** Comprador123!

---

## 🎯 Fluxo de Trabalho Recomendado

### Dia a dia
```bash
# 1. Iniciar banco (Docker)
make docker-up

# 2. Popular dados de exemplo (se necessário)
make seed

# 3. Iniciar servidor de desenvolvimento
make dev

# Em outro terminal:
# 4. Iniciar worker Celery
make run-worker
```

### Antes de commit
```bash
# 1. Executar linter
make lint

# 2. Executar testes
make test

# 3. Limpar arquivos temporários
make clean
```

### Deploy local
```bash
# Build completo
make deploy-local
```

---

## 🔍 Troubleshooting

### App não inicia
```bash
# Verificar variáveis de ambiente
make env-check

# Gerar nova SECRET_KEY
make secret-key
```

### Testes falhando
```bash
# Resetar banco e recriar seed
make db-reset
make seed
```

### Worker não processa tarefas
```bash
# Reiniciar worker
# Ctrl+C no terminal atual
make run-worker
```

---

## 📝 Ajuda

### Listar todos os comandos
```bash
make help
```

### Ver código fonte dos comandos
```bash
cat Makefile
```

---

**Última atualização:** Março 2026  
**Versão:** 1.0
