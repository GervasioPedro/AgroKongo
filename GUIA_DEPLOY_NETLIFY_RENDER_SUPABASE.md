# Guia de Deploy: Netlify + Render + Supabase

Este guia detalha como fazer o deploy da aplicação AgroKongo usando a stack Netlify (frontend), Render (backend) e Supabase (base de dados e armazenamento).

## Visão Geral da Arquitetura

*   **Frontend (Netlify)**: O seu frontend (React, Vue, Angular, etc.) será hospedado na Netlify. Ele fará chamadas de API para o backend no Render.
*   **Backend (Render)**: A sua aplicação Flask (API), os workers Celery e o Celery Beat serão hospedados no Render.
*   **Base de Dados (Supabase)**: Usaremos o PostgreSQL do Supabase como a nossa base de dados principal.
*   **Armazenamento de Ficheiros (Supabase)**: Usaremos o Supabase Storage para guardar os uploads de ficheiros (imagens de perfil, safras, etc.).

## Passo 1: Configurar o Supabase

1.  **Criar um Projeto no Supabase**:
    *   Vá para [supabase.com](https://supabase.com/) e crie um novo projeto.
    *   Guarde a sua **senha da base de dados** num local seguro.
2.  **Obter as Credenciais da Base de Dados**:
    *   No dashboard do Supabase, vá para **Project Settings > Database**.
    *   Encontre a sua **Connection String** (URI). Será algo como `postgresql://postgres:[YOUR-PASSWORD]@[HOST]:[PORT]/postgres`.
3.  **Configurar o Armazenamento (Storage)**:
    *   No menu lateral, vá para **Storage**.
    *   Crie um novo **Bucket** chamado `agrokongo-uploads`.
    *   **Importante**: Defina as políticas de acesso (RLS) para este bucket. Para começar, pode criar uma política que permita o acesso público para leitura (`SELECT`) e acesso autenticado para escrita (`INSERT`, `UPDATE`, `DELETE`).
4.  **Obter as Credenciais do Supabase**:
    *   Vá para **Project Settings > API**.
    *   Guarde os seguintes valores:
        *   **Project URL** (`SUPABASE_URL`)
        *   **`service_role` key** (`SUPABASE_SERVICE_ROLE`)
        *   **Public URL** (para o Supabase Storage, será algo como `https://<proj>.supabase.co/storage/v1`)

## Passo 2: Configurar o Backend no Render

1.  **Criar uma Conta no Render**:
    *   Vá para [render.com](https://render.com/) e crie uma conta.
2.  **Criar um Novo "Blueprint"**:
    *   No dashboard do Render, vá para **Blueprints** e clique em **New Blueprint**.
    *   Conecte o seu repositório do GitHub/GitLab.
    *   O Render irá detetar automaticamente o seu ficheiro `render.yaml`.
3.  **Rever os Serviços**:
    *   O Render irá mostrar os serviços que ele planeia criar com base no `render.yaml`:
        *   `agrokongo-api` (Web Service)
        *   `agrokongo-worker` (Worker)
        *   `agrokongo-beat` (Worker)
        *   `agrokongo-db` (PostgreSQL Database) - **Vamos substituir este pelo Supabase.**
        *   `agrokongo-redis` (Redis)
4.  **Ajustar a Configuração da Base de Dados**:
    *   **Exclua a base de dados do Render**: No `render.yaml`, pode remover a secção `databases` que define `agrokongo-db`.
    *   **Adicione a URL do Supabase**: No dashboard do Render, vá para as **Environment Variables** do serviço `agrokongo-api` (e dos workers) e adicione a variável `DATABASE_URL` com a connection string do Supabase que guardou no Passo 1.
5.  **Preencher as Variáveis de Ambiente**:
    *   No dashboard do Render, para cada serviço (`agrokongo-api`, `agrokongo-worker`, `agrokongo-beat`), vá para a secção **Environment** e adicione/atualize as seguintes variáveis:
        *   `DATABASE_URL`: A connection string do Supabase.
        *   `SECRET_KEY`: O Render irá gerar uma, mas certifique-se de que está sincronizada (`sync: true`).
        *   `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`: As suas credenciais de e-mail.
        *   `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE`, `SUPABASE_PUBLIC_URL`: As credenciais do Supabase que guardou.
        *   `CORS_ORIGINS`: Verifique se os domínios estão corretos (ex: `https://seu-site.netlify.app`).
6.  **Fazer o Deploy**:
    *   Clique em **Apply** ou **Create** para iniciar o deploy.
    *   O Render irá instalar as dependências, executar as migrações (`flask db upgrade`) e iniciar os serviços.
    *   Acompanhe os logs para verificar se há erros.

## Passo 3: Configurar o Frontend na Netlify

1.  **Criar uma Conta na Netlify**:
    *   Vá para [netlify.com](https://netlify.com/) e crie uma conta.
2.  **Adicionar um Novo Site**:
    *   No dashboard da Netlify, clique em **Add new site > Import an existing project**.
    *   Conecte o seu repositório do GitHub/GitLab (o mesmo que usou no Render).
3.  **Configurar as Definições de Build**:
    *   **Build command**: O comando para construir o seu frontend (ex: `npm run build`, `yarn build`).
    *   **Publish directory**: O diretório onde o seu frontend construído é guardado (ex: `dist`, `build`).
4.  **Adicionar Variáveis de Ambiente**:
    *   Vá para **Site settings > Build & deploy > Environment**.
    *   Adicione a seguinte variável de ambiente:
        *   `VITE_API_URL` (ou `REACT_APP_API_URL`, etc., dependendo do seu frontend): A URL da sua API no Render (ex: `https://agrokongo-api.onrender.com`).
5.  **Fazer o Deploy**:
    *   Clique em **Deploy site**.
    *   A Netlify irá construir e fazer o deploy do seu frontend.

## Passo 4: Pós-Deploy

1.  **Verificar a Conexão Frontend-Backend**:
    *   Abra o seu site na Netlify.
    *   Use as ferramentas de desenvolvedor do navegador para verificar se as chamadas de API para o backend no Render estão a funcionar corretamente (sem erros de CORS).
2.  **Testar as Funcionalidades**:
    *   Faça um teste completo de ponta a ponta: registo, login, criação de safra, upload de imagem (verifique no Supabase Storage), etc.
3.  **Configurar Domínios Personalizados**:
    *   Adicione os seus domínios personalizados tanto no Render (para a API) quanto na Netlify (para o frontend).

---

**Parabéns!** Se seguiu todos os passos, a sua aplicação deve estar a funcionar em produção com uma stack moderna e escalável.
