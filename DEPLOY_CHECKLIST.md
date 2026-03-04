# Checklist de Deploy para AgroKongo

Este documento detalha os passos essenciais para realizar o deploy da aplicação AgroKongo em ambiente de produção.

## Pré-requisitos

1.  **Ambiente de Produção**: Servidor ou plataforma PaaS (Render, Heroku, AWS Elastic Beanstalk, etc.) configurado.
2.  **Base de Dados PostgreSQL**: Instância de DB acessível, com credenciais e URL de conexão.
3.  **Redis**: Instância de Redis acessível, com credenciais e URL de conexão (para Celery e Cache).
4.  **Variáveis de Ambiente**: Todas as variáveis de ambiente necessárias definidas no ambiente de produção.
5.  **Domínio**: Domínio configurado e apontado para o servidor/balanceador de carga.
6.  **Certificado SSL/TLS**: Configurado para HTTPS.

## Variáveis de Ambiente Essenciais (Exemplo)

Certifique-se de que as seguintes variáveis de ambiente estão definidas no seu ambiente de produção:

*   `FLASK_ENV=production`
*   `SECRET_KEY=<sua_secret_key_segura>` (Gerar uma nova para produção)
*   `DATABASE_URL=postgresql://user:pass@host:port/dbname`
*   `REDIS_URL=redis://:password@host:port/db_number`
*   `MAIL_SERVER=<seu_servidor_smtp>`
*   `MAIL_PORT=<porta_smtp>`
*   `MAIL_USE_TLS=True`
*   `MAIL_USERNAME=<seu_email>`
*   `MAIL_PASSWORD=<sua_senha_email>`
*   `UPLOAD_PATH=/path/to/data_storage` (ou configurar Supabase)
*   `SUPABASE_URL=<url_supabase>` (se usar)
*   `SUPABASE_SERVICE_ROLE=<supabase_service_role_key>` (se usar)
*   `SUPABASE_BUCKET=agrokongo-uploads` (se usar)
*   `SUPABASE_PUBLIC_URL=<url_publica_supabase>` (se usar)
*   `CORS_ORIGINS=https://www.agrokongo.ao,https://agrokongo.netlify.app` (domínios permitidos)
*   `ITEMS_PER_PAGE=10` (ou outro valor)
*   `CELERY_CONCURRENCY=2` (ou outro valor, dependendo dos recursos do worker)

## Passos do Deploy

### 1. Preparação do Código

1.  **Limpeza de Ficheiros**:
    *   **APAGUE** os ficheiros redundantes: `app/routes/comprador_v2.py`, `app/routes/comprador_api.py`, `app/routes/comprador_fixed.py`, `app/routes/produtor_fixed.py`, `app/routes/mercado_fixed.py`, `app/routes/disputas_fixed.py`, `app/routes/main_fixed.py` e quaisquer ficheiros `.backup_*`.
2.  **Atualizar Dependências (Opcional, mas Recomendado)**:
    *   Se tiver um `requirements-dev.txt`, certifique-se de que o `requirements.txt` contém apenas as dependências de produção.
    *   Execute `pip install -r requirements.txt` localmente para garantir que todas as dependências estão instaladas e que não há conflitos.
3.  **Testes Finais**:
    *   Execute a suíte de testes completa (`pytest`) para garantir que todas as funcionalidades estão a funcionar como esperado.
    *   `pytest tests/`

### 2. Configuração do Ambiente de Produção

1.  **Definir Variáveis de Ambiente**: Configure todas as variáveis de ambiente listadas acima no seu ambiente de deploy.
2.  **Instalar Dependências**: No servidor de produção, instale as dependências Python:
    *   `pip install -r requirements.txt`
3.  **Migrações da Base de Dados**:
    *   Certifique-se de que a base de dados está acessível e as credenciais estão corretas.
    *   Execute as migrações para aplicar quaisquer alterações no esquema da base de dados:
        *   `flask db upgrade`
    *   **Importante**: Faça backup da sua base de dados antes de executar migrações em produção.
4.  **Criação de Diretórios de Upload**:
    *   Se estiver a usar armazenamento local, crie os diretórios necessários para uploads (ex: `data_storage/public/safras`, `data_storage/private/comprovativos`).
    *   `mkdir -p data_storage/public/safras data_storage/public/perfil data_storage/private/comprovativos`

### 3. Iniciar a Aplicação

A aplicação AgroKongo é composta por três tipos de processos, conforme definido no `Procfile`:

1.  **Processo Web (Gunicorn)**:
    *   Inicia o servidor web que serve as requisições HTTP.
    *   Comando: `gunicorn run:app --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT`
    *   **Recomendação**: Use um gestor de processos (systemd, Supervisor) para garantir que o Gunicorn é reiniciado automaticamente em caso de falha.
2.  **Worker Celery**:
    *   Processa tarefas assíncronas em segundo plano.
    *   Comando: `celery -A celery_worker.celery worker --loglevel=info --concurrency=2`
    *   **Recomendação**: Execute múltiplos workers Celery e monitorize as filas.
3.  **Celery Beat**:
    *   Agenda e dispara tarefas periódicas (ex: auditoria de pagamentos).
    *   Comando: `celery -A celery_worker.celery beat --loglevel=info`
    *   **Recomendação**: Apenas uma instância do Celery Beat deve estar ativa para evitar duplicação de tarefas.

### 4. Configuração Adicional (Dependendo do Ambiente)

*   **Nginx/Apache (se usar)**: Configure o servidor web para atuar como um proxy reverso para o Gunicorn, gerir SSL/TLS e servir ficheiros estáticos.
*   **Balanceador de Carga**: Se estiver a executar múltiplas instâncias da aplicação, configure um balanceador de carga.
*   **Firewall**: Configure as regras de firewall para permitir apenas o tráfego necessário.
*   **Monitorização e Logging**: Configure ferramentas de monitorização (APM, logs centralizados) para observar a saúde e performance da aplicação em tempo real.

## Pós-Deploy

1.  **Verificação de Saúde**:
    *   Aceda à URL da aplicação no navegador.
    *   Verifique os logs da aplicação, Gunicorn e Celery para quaisquer erros.
    *   Teste as principais funcionalidades (login, registo, criação de safra, compra, etc.).
2.  **Testes de Carga (Opcional)**:
    *   Realize testes de carga para garantir que a aplicação se comporta bem sob stress.

---

**Parabéns! O seu projeto está agora pronto para ser lançado.**
