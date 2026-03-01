AgroKongo 🚜🇦🇴
Conectando a Terra ao Mercado com Segurança.

O AgroKongo é uma plataforma de intermediação agrícola focada no mercado angolano, resolvendo o problema da falta de confiança entre produtores rurais e compradores urbanos através de um sistema de Escrow (Custódia Financeira).

🛡️ O Diferencial: Escrow Inteligente
Diferente de um classificado comum, aqui o dinheiro é protegido:

Validação Humana: Administradores conferem talões bancários antes de autorizar o envio.

Proteção ao Produtor: O agricultor só colhe/envia quando o sistema garante que o dinheiro já está em custódia.

Confirmação de Receção: O valor só é liquidado ao produtor após o comprador confirmar que a mercadoria chegou em condições.

Resolução de Disputas: Mediação administrativa para casos de quebra de contrato.

🏗️ Arquitetura e Tech Stack
Para garantir que o sistema não falhe durante picos de safra, utilizamos:

Core: Python 3.11 / Flask (Padrão Application Factory)

Base de Dados: PostgreSQL (Integridade e Escala)

Background Jobs: Celery + Redis (Processamento de faturas e auditoria automática)

Segurança: Flask-Talisman (HTTPS), Flask-Limiter e Auditoria de Logs imutável.

Infraestrutura: Docker & Docker Compose.

📦 Instalação e Deploy (Via Docker)
A forma mais rápida e segura de rodar o AgroKongo é através de containers:

Clone o Repositório:

Bash
git clone https://github.com/teu-usuario/agrokongo.git
cd agrokongo
Configure as Variáveis de Ambiente: Crie um ficheiro .env na raiz:

Code snippet
SECRET_KEY=sua_chave_ultra_secreta
DATABASE_URL=postgresql://agrokongo:senha_segura@db:5432/agrokongo
REDIS_URL=redis://redis:6379/0
FLASK_ENV=production
Suba a Infraestrutura:

Bash
docker-compose up -d --build
Este comando levanta o Web Server, a DB Postgres, o Redis e o Worker do Celery automaticamente.

Aceda à Aplicação: O sistema estará disponível em http://localhost:5000 (ou porta 80, conforme configurado).

📊 Estrutura de Pastas
Plaintext
├── app/                # Código fonte da aplicação
│   ├── models/         # Modelos de dados e lógica de negócio
│   ├── routes/         # Blueprints (Admin, Produtor, Comprador)
│   ├── tasks.py        # Tarefas assíncronas (Celery)
│   └── utils/          # Helpers (Otimização de imagem, etc)
├── data_storage/       # Volumes persistentes (Imagens e PDFs)
├── docker-compose.yml  # Orquestração de serviços
├── Dockerfile          # Definição do container principal
└── run.py              # Entry point da aplicação