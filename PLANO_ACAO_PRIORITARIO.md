# 🎯 PLANO DE AÇÃO PRIORITÁRIO - AGROKONGO 2026

**Priorização:** Crítico → Alto → Médio → Baixo  
**Horizonte:** 90 dias (1 semana a 3 meses)

---

## 🔴 PRIORIDADE 1: CRÍTICO (Semana 1-2)

### Ação 1.1: Implementar Índices de Database ⚡

**Por quê:** Queries lentas estão impactando performance em 50-80%

**O quê:**
```sql
-- Adicionar índices estratégicos
CREATE INDEX idx_transacao_status ON transacoes(status);
CREATE INDEX idx_transacao_comprador_status ON transacoes(comprador_id, status);
CREATE INDEX idx_safra_produto_status ON safras(produto_id, status);
CREATE INDEX idx_usuario_tipo_validado ON usuarios(tipo, conta_validada);
```

**Como:**
1. Criar migration Alembic:
```bash
flask db migrate -m "Add strategic indexes for performance"
```

2. Aplicar migration:
```bash
flask db upgrade
```

3. Validar performance:
```python
# Testar queries antes/depois
import time

start = time.time()
Transacao.query.filter_by(status='pendente').all()
print(f"Tempo: {time.time() - start:.3f}s")
# Antes: ~0.5s | Depois: ~0.01s ✅
```

**Responsável:** Backend Team  
**Prazo:** 2 dias  
**Impacto:** ⭐⭐⭐⭐⭐ (Alto)  
**Esforço:** Baixo

---

### Ação 1.2: Aumentar Cobertura de Testes para 60% 🧪

**Por quê:** 35% atual é insuficiente para produção (bugs passando)

**O quê:** Focar em módulos críticos primeiro

**Plano:**

#### Semana 1: Módulo de Pagamentos (20% → 40%)
```python
# tests/integration/test_pagamentos.py

class TestPagamentoCritico:
    def test_criar_transacao_com_escrow(self):
        """Garante que dinheiro vai para escrow"""
        transacao = Transacao(
            safra_id=safra.id,
            comprador_id=comprador.id,
            vendedor_id=produtor.id,
            valor_total=Decimal('1500.00')
        )
        assert transacao.valor_em_escrow == Decimal('1500.00')
    
    def test_liberar_pagamento_apos_confirmacao(self):
        """Só libera após comprador confirmar recebimento"""
        transacao.status = 'enviado'
        transacao.confirmar_recebimento()
        assert transacao.status == 'finalizada'
        assert produtor.saldo_disponivel += transacao.valor
    
    def test_estornar_pagamento_em_disputa(self):
        """Protege comprador em caso de disputa"""
        disputa = Disputa(transacao_id=transacao.id, motivo="Produto não entregue")
        transacao.estornar_pagamento()
        assert comprador.saldo_disponivel += transacao.valor
```

#### Semana 2: Módulo de Autenticação (40% → 60%)
```python
# tests/integration/test_auth.py

class TestAuthSeguranca:
    def test_csrf_obrigatorio_em_login(self):
        """Rejeita login sem CSRF token"""
        response = client.post('/login', data={
            'telemovel': '912345678',
            'senha': '123456'
            # Sem CSRF token
        })
        assert response.status_code == 403
    
    def test_rate_limit_prevencao_brute_force(self):
        """Bloqueia após 5 tentativas"""
        for i in range(5):
            client.post('/login', dados_incorretos)
        
        # 6ª tentativa deve ser bloqueada
        response = client.post('/login', dados_corretos)
        assert response.status_code == 429  # Too Many Requests
```

**Responsável:** QA Team  
**Prazo:** 10 dias  
**Impacto:** ⭐⭐⭐⭐⭐ (Crítico)  
**Esforço:** Médio

---

### Ação 1.3: Unificar Estratégia de Frontend 🎨

**Por quê:** Manter dois frontends duplica esforço em 40%

**Decisão:** Migrar gradualmente para **Next.js** (moderno, escalável)

**Plano de Migração (6 semanas):**

#### Semana 1-2: Parar Sangria
```markdown
[✓] Congelar criação de novos templates Jinja2
[✓] Todas features novas apenas em Next.js
[✓] Documentar decisão para equipe
```

#### Semana 3-4: Migrar Páginas Críticas
```markdown
[ ] Dashboard Produtor → Next.js
[ ] Dashboard Comprador → Next.js
[ ] Lista de Safras (Marketplace) → Next.js
[ ] Detalhes da Transação → Next.js
```

#### Semana 5-6: Remover Legado
```markdown
[ ] Redirecionar rotas Jinja2 para Next.js
[ ] Remover templates não utilizados
[ ] Limpar imports mortos
```

**Exemplo de Migração:**
```tsx
// frontend/src/app/produtor/dashboard/page.tsx
export default function DashboardProdutor() {
  const { data, isLoading } = useSWR('/api/produtor/dashboard');
  
  if (isLoading) return <Loading />;
  
  return (
    <div className="grid gap-6">
      <KPICard title="Vendas" value={data.vendas} />
      <KPICard title="Receita" value={data.receita} />
      {/* ... */}
    </div>
  );
}
```

**Responsável:** Frontend Team  
**Prazo:** 6 semanas  
**Impacto:** ⭐⭐⭐⭐ (Alto)  
**Esforço:** Alto

---

## 🟡 PRIORIDADE 2: ALTO (Mês 1-2)

### Ação 2.1: Migrar Scheduler para Celery ⏰

**Por quê:** Tarefas síncronas bloqueiam processo web

**Atual (Problemático):**
```python
# app/__init__.py
scheduler = APScheduler()

scheduler.add_job(
    func=monitorar_pagamentos,  # Bloqueia request
    trigger='interval',
    hours=1
)
```

**Novo (Assíncrono):**
```python
# app/tasks/monitoramento.py
@celery.task(bind=True, max_retries=3)
def monitorar_pagamentos(self):
    try:
        transacoes_estagnadas = Transacao.query.filter(
            Transacao.status == TransactionStatus.ANALISE,
            Transacao.data_criacao <= datetime.now(timezone.utc) - timedelta(hours=24)
        ).all()
        
        for t in transacoes_estagnadas:
            notificar_admin(t)
            
    except Exception as e:
        # Retry automático
        raise self.retry(exc=e, countdown=300)
```

**Agendamento:**
```python
# celery_beat schedule
CELERY_BEAT_SCHEDULE = {
    'monitor-pagamentos': {
        'task': 'app.tasks.monitoramento.monitorar_pagamentos',
        'schedule': crontab(minute=0),  # Toda hora
    },
}
```

**Benefícios:**
- ✅ Não bloqueia requests web
- ✅ Retry automático em falhas
- ✅ Monitorização via Flower
- ✅ Escala horizontal

**Responsável:** Backend Team  
**Prazo:** 1 semana  
**Impacto:** ⭐⭐⭐⭐ (Alto)  
**Esforço:** Baixo

---

### Ação 2.2: Implementar Cache de Longo Prazo 💾

**Por quê:** Queries repetitivas desperdiçam recursos

**Oportunidades:**

#### 1. Cache de Produtos Estáticos (5min → 1h)
```python
# app/routes/api_v1.py
@api_v1_bp.route('/produtos', methods=['GET'])
@cache.cached(timeout=3600)  # 1 hora
def listar_produtos():
    return Produto.query.filter_by(ativo=True).all()
```

#### 2. Cache de Estatísticas (10min → 1h)
```python
@api_v1_bp.route('/estatisticas', methods=['GET'])
@cache.cached(timeout=3600)
def estatisticas():
    stats = {
        'produtores_ativos': Usuario.query.filter_by(
            tipo='produtor', conta_validada=True
        ).count(),
        'transacoes_concluidas': Transacao.query.filter_by(
            status='finalizada'
        ).count(),
    }
    return stats
```

#### 3. Cache de Perfil de Usuário (fragmento)
```python
# Cache seletivo de dados que mudam pouco
@cache.cached(timeout=300, key_prefix='user_profile_{user_id}')
def get_user_profile(user_id):
    user = Usuario.query.get(user_id)
    return {
        'nome': user.nome,
        'foto_perfil': user.foto_perfil,
        'vendas_concluidas': user.vendas_concluidas,
    }
```

**Invalidação de Cache:**
```python
# Invalidar cache quando dado mudar
def atualizar_perfil(usuario_id, novos_dados):
    usuario = Usuario.query.get(usuario_id)
    usuario.nome = novos_dados['nome']
    db.session.commit()
    
    # Invalidar cache
    cache.delete(f'user_profile_{usuario_id}')
```

**Impacto Estimado:**
- 70% redução em queries repetitivas
- Response time: 200ms → 50ms
- DB load: -60%

**Responsável:** Backend Team  
**Prazo:** 3 dias  
**Impacto:** ⭐⭐⭐⭐ (Alto)  
**Esforço:** Baixo

---

### Ação 2.3: Configurar API Gateway 🚪

**Por quê:** Centralizar gestão de APIs, versionamento, segurança

**Opções:**

#### Opção A: Kong (Open Source)
```yaml
# docker-compose.yml
services:
  kong:
    image: kong:3.0
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/kong.yml
    volumes:
      - ./kong:/kong
  
  agrokongo-api:
    # Serviço existente
```

```yaml
# kong/kong.yml
services:
  - name: agrokongo-v1
    url: http://agrokongo-api:5000/api/v1
    routes:
      - paths: [/api/v1]
        strip_path: false
    
plugins:
  - name: rate-limiting
    config:
      minute: 100
      policy: redis
  - name: cors
    config:
      origins: [https://agrokongo.netlify.app]
```

#### Opção B: AWS API Gateway (Managed)
```yaml
# serverless.yml
service: agrokongo-api

provider:
  name: aws
  runtime: python3.11

functions:
  - health:
      handler: run.health
      events:
        - http:
            path: /api/v1/health
            method: get
            cors: true
```

**Benefícios:**
- ✅ Versionamento (/v1, /v2)
- ✅ Rate limiting centralizado
- ✅ Circuit breaker
- ✅ Logging unificado
- ✅ Analytics de uso

**Responsável:** DevOps Team  
**Prazo:** 2 semanas  
**Impacto:** ⭐⭐⭐⭐ (Alto)  
**Esforço:** Alto

---

## 🟢 PRIORIDADE 3: MÉDIO (Mês 2-3)

### Ação 3.1: Setup de Monitorização 📊

**Por quê:** Sem monitorização, problemas passam despercebidos

**Stack Recomendada:**

#### 1. Sentry (Erros em Tempo Real)
```python
# requirements.txt
sentry-sdk[flask]==1.20.0

# run.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
    environment=os.environ.get('FLASK_ENV', 'development')
)
```

**Dashboard:**
- Erros por tipo
- Users afetados
- Release que introduziu bug
- Performance de endpoints

#### 2. Prometheus + Grafana (Métricas)
```python
# requirements.txt
prometheus-client==0.16.0

# app/__init__.py
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)

@metrics.counter('http_requests_total', 'Total HTTP requests',
                 labels={'status': lambda r: r.status_code})
```

**Métricas para Trackear:**
- Request rate (req/s)
- Error rate (%)
- Response time (p50, p95, p99)
- DB query time
- Memory/CPU usage

#### 3. Slack Alerts (Notificações)
```python
# app/utils/alerts.py
def enviar_alerta_slack(mensagem, canal='#alerts'):
    payload = {
        'text': f'🚨 ALERTA: {mensagem}',
        'channel': canal,
        'username': 'AgroKongo Bot'
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

# Uso em handlers de erro
@app.errorhandler(500)
def error_500(error):
    enviar_alerta_slack(f"Erro 500: {request.path}")
```

**Responsável:** DevOps Team  
**Prazo:** 1 semana  
**Impacto:** ⭐⭐⭐⭐⭐ (Crítico)  
**Esforço:** Médio

---

### Ação 3.2: CDN para Imagens 🌐

**Por quê:** Latência de imagens está alta (200ms+)

**Opção A: Cloudflare (Recomendado)**
```markdown
[✓] Configurar DNS no Cloudflare
[✓] Ativar proxy (nuvem laranja)
[✓] Configurar Cache Rules:
    - Images: Cache 1 month
    - PDFs: Cache 1 week
[✓] Habilitar Polish (otimização automática)
```

**Configuração DNS:**
```
Type: CNAME
Name: cdn
Content: agrokongo.netlify.app
Proxy: Enabled (orange cloud)
```

**URL Mapping:**
```python
# config.py
CDN_URL = os.environ.get('CDN_URL', 'https://cdn.agrokongo.ao')

# Templates
<img src="{{ config.CDN_URL }}/media/publico/safras/{{ imagem }}" />
```

**Benefícios:**
- ✅ Latência: 200ms → 20ms
- ✅ Offload de tráfego do servidor
- ✅ Otimização automática de imagens
- ✅ DDoS protection inclusa

**Responsável:** DevOps Team  
**Prazo:** 2 dias  
**Impacto:** ⭐⭐⭐⭐ (Alto)  
**Esforço:** Baixo

---

### Ação 3.3: Extrair Serviço de Autenticação 🔐

**Por quê:** Primeiro passo para microserviços

**Escopo:**
```
[Auth Service]
├── Login/Logout
├── Registro
├── Reset de Senha
├── JWT Token Emission
└── User Profile
```

**Estrutura:**
```
auth-service/
├── app/
│   ├── routes/
│   │   └── auth.py
│   ├── models/
│   │   └── usuario.py
│   └── services/
│       └── jwt_service.py
├── Dockerfile
├── requirements.txt
└── run.py
```

**API:**
```python
# POST /auth/login
{
  "telemovel": "912345678",
  "senha": "..."
}

# Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "dGhpcyBpcyBhIHJlZnJl...",
  "user": {
    "id": 1,
    "nome": "João Manuel",
    "tipo": "produtor"
  }
}
```

**Comunicação:**
```python
# Main app chama auth service
import requests

AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL')

def authenticate_user(telemovel, senha):
    response = requests.post(f'{AUTH_SERVICE_URL}/auth/login', json={
        'telemovel': telemovel,
        'senha': senha
    })
    return response.json()
```

**Benefícios:**
- ✅ Deploy independente
- ✅ Escala sob carga (login em massa)
- ✅ Tecnologia específica (pode usar FastAPI)
- ✅ Falha isolada (não derruba todo sistema)

**Responsável:** Backend Team  
**Prazo:** 3 semanas  
**Impacto:** ⭐⭐⭐⭐ (Alto)  
**Esforço:** Alto

---

## 📊 MATRIZ DE PRIORIZAÇÃO

| Ação | Impacto | Esforço | ROI | Prazo |
|------|---------|---------|-----|-------|
| **1.1 Índices DB** | ⭐⭐⭐⭐⭐ | Baixo | ⭐⭐⭐⭐⭐ | 2 dias |
| **1.2 Testes (60%)** | ⭐⭐⭐⭐⭐ | Médio | ⭐⭐⭐⭐⭐ | 10 dias |
| **1.3 Unificar Frontend** | ⭐⭐⭐⭐ | Alto | ⭐⭐⭐⭐ | 6 semanas |
| **2.1 Scheduler → Celery** | ⭐⭐⭐⭐ | Baixo | ⭐⭐⭐⭐ | 1 semana |
| **2.2 Cache** | ⭐⭐⭐⭐ | Baixo | ⭐⭐⭐⭐⭐ | 3 dias |
| **2.3 API Gateway** | ⭐⭐⭐⭐ | Alto | ⭐⭐⭐ | 2 semanas |
| **3.1 Monitorização** | ⭐⭐⭐⭐⭐ | Médio | ⭐⭐⭐⭐⭐ | 1 semana |
| **3.2 CDN** | ⭐⭐⭐⭐ | Baixo | ⭐⭐⭐⭐ | 2 dias |
| **3.3 Auth Service** | ⭐⭐⭐⭐ | Alto | ⭐⭐⭐ | 3 semanas |

---

## 🎯 CHECKLIST SEMANAL

### Semana 1 (Foco: Database + Testes)
```markdown
[ ] Criar migration de índices
[ ] Aplicar índices em produção
[ ] Validar performance (antes/depois)
[ ] Criar 10 testes de pagamento
[ ] Criar 5 testes de autenticação
[ ] Medir cobertura (meta: 45%)
```

### Semana 2 (Foco: Testes + Cache)
```markdown
[ ] Criar 10 testes de disputas
[ ] Criar 5 testes de safras
[ ] Implementar cache de produtos
[ ] Implementar cache de estatísticas
[ ] Medir cobertura (meta: 60%)
[ ] Validar hit rate de cache (>70%)
```

### Semana 3 (Foco: Frontend + Scheduler)
```markdown
[ ] Congelar novos templates Jinja2
[ ] Migrar dashboard produtor para Next.js
[ ] Migrar lista de safras para Next.js
[ ] Converter scheduler para Celery
[ ] Configurar Celery Beat
[ ] Testar tarefas agendadas
```

### Semana 4 (Foco: Monitorização)
```markdown
[ ] Configurar Sentry
[ ] Configurar Prometheus
[ ] Configurar Grafana dashboards
[ ] Setup Slack alerts
[ ] Testar alertas de erro 500
[ ] Documentar runbooks
```

---

## 📈 METAS DE CURTO PRAZO

### 30 Dias
- [ ] Cobertura de testes: 60%
- [ ] Todos índices implementados
- [ ] Cache operando (hit rate >70%)
- [ ] Scheduler 100% Celery
- [ ] Sentry configurado

### 60 Dias
- [ ] Frontend unificado (Next.js)
- [ ] API Gateway em produção
- [ ] CDN configurado
- [ ] Monitorização completa

### 90 Dias
- [ ] Auth service operando
- [ ] Cobertura de testes: 80%
- [ ] Response time médio: <100ms
- [ ] Uptime: 99.5%

---

## 🚀 COMEÇAR AGORA

### Passo 1: Setup Ambiente (Hoje)
```bash
# Clonar repositório
git clone https://github.com/agrokongo/agrokongo.git
cd agrokongo

# Criar branch para primeira melhoria
git checkout -b feature/add-database-indexes

# Instalar dependências
pip install -r requirements.txt
```

### Passo 2: Primeira Melhoria (Dia 1-2)
```bash
# Gerar migration de índices
flask db migrate -m "Add strategic indexes"

# Revisar migration gerado
cat migrations/versions/001_add_indexes.py

# Aplicar em desenvolvimento
flask db upgrade

# Testar performance
python scripts/test_query_performance.py
```

### Passo 3: Commit e Deploy (Dia 2)
```bash
# Commit
git add .
git commit -m "feat: Add database indexes for performance improvement"
git push origin feature/add-database-indexes

# Pull request
# Revisar com equipe
# Merge em main

# Deploy em produção
git checkout main
git pull
flask db upgrade
```

---

**Documento de Ação Criado:** Março 2026  
**Próxima Review:** 7 dias  
**Responsável pela Execução:** Tech Lead
