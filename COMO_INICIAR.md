# 🚀 Como Iniciar o Projeto AgroKongo

## Pré-requisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis

---

## 1️⃣ Iniciar o Backend (Flask)

### Passo 1: Ativar o ambiente virtual
```bash
# No diretório raiz do projeto
.venv312\Scripts\activate
```

### Passo 2: Configurar variáveis de ambiente
Certifica-te que o ficheiro `.env` existe na raiz com:
```env
SECRET_KEY=sua_chave_ultra_secreta
DATABASE_URL=postgresql://agrokongo:senha_segura@localhost:5432/agrokongo
REDIS_URL=redis://localhost:6379/0
FLASK_ENV=development
```

### Passo 3: Iniciar serviços necessários
```bash
# Iniciar PostgreSQL (se não estiver a correr)
# Iniciar Redis (se não estiver a correr)
redis-server
```

### Passo 4: Executar migrações da base de dados
```bash
flask db upgrade
```

### Passo 5: Iniciar o servidor Flask
```bash
python run.py
```
**O backend estará disponível em:** `http://127.0.0.1:5000`

---

## 2️⃣ Iniciar o Frontend (Next.js)

### Passo 1: Navegar para a pasta frontend
```bash
cd frontend
```

### Passo 2: Instalar dependências (primeira vez)
```bash
npm install
```

### Passo 3: Configurar variáveis de ambiente
Certifica-te que o ficheiro `.env.local` existe em `frontend/` com:
```env
BACKEND_BASE_URL=http://127.0.0.1:5000
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

### Passo 4: Iniciar o servidor Next.js
```bash
npm run dev
```
**O frontend estará disponível em:** `http://localhost:3000`

---

## 3️⃣ Iniciar Worker Celery (Opcional - para tarefas assíncronas)

### Em outro terminal, com o ambiente virtual ativado:
```bash
celery -A app.celery worker --loglevel=info
```

---

## 📋 Ordem Recomendada de Inicialização

1. **PostgreSQL** (base de dados)
2. **Redis** (cache e filas)
3. **Backend Flask** (API)
4. **Worker Celery** (tarefas assíncronas)
5. **Frontend Next.js** (interface)

---

## 🔍 Verificar se está tudo a funcionar

### Backend:
```bash
curl http://127.0.0.1:5000/health
```

### Frontend:
Abrir no navegador: `http://localhost:3000`

---

## 🛑 Parar os Serviços

- **Backend/Frontend**: `Ctrl + C` no terminal
- **Redis**: `redis-cli shutdown`
- **PostgreSQL**: Depende da instalação

---

## 📝 Comandos Úteis

### Backend:
```bash
# Criar nova migração
flask db migrate -m "descrição"

# Aplicar migrações
flask db upgrade

# Reverter migração
flask db downgrade

# Abrir shell Python com contexto da app
flask shell
```

### Frontend:
```bash
# Build para produção
npm run build

# Iniciar em modo produção
npm start

# Verificar tipos TypeScript
npm run type-check

# Lint do código
npm run lint
```

---

## 🐛 Resolução de Problemas

### Erro: "Port 5000 already in use"
```bash
# Windows
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

### Erro: "Port 3000 already in use"
```bash
# Windows
netstat -ano | findstr :3000
taskkill /F /PID <PID>
```

### Erro: "Cannot connect to database"
- Verifica se o PostgreSQL está a correr
- Confirma as credenciais no `.env`

### Erro: "Cannot connect to Redis"
- Verifica se o Redis está a correr: `redis-cli ping`

---

## 📦 Estrutura do Projeto

```
agrokongoVS/
├── app/                    # Backend Flask
│   ├── models/            # Modelos de dados
│   ├── routes/            # Rotas da API
│   ├── tasks/             # Tarefas Celery
│   └── utils/             # Utilitários
├── frontend/              # Frontend Next.js
│   └── src/
│       ├── app/           # Páginas e rotas
│       ├── components/    # Componentes React
│       ├── services/      # Serviços API
│       └── store/         # Estado global (Zustand)
├── migrations/            # Migrações da BD
├── .env                   # Variáveis backend
└── run.py                 # Entry point backend
```

---

## 🎯 Acesso Rápido

- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:5000
- **Health Check**: http://127.0.0.1:5000/health
- **Documentação API**: http://127.0.0.1:5000/api/docs (se configurado)

---

**Desenvolvido com ❤️ para o mercado agrícola angolano**
