# 🔧 RECOMENDAÇÕES TÉCNICAS - AGROKONGO

## 1. CORREÇÕES CRÍTICAS DE SEGURANÇA

### 1.1 Rate Limiting em Endpoints Sensíveis

```python
# app/extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"
)

def setup_extensions(app):
    # ... código existente ...
    limiter.init_app(app)
```

```python
# app/routes/auth.py
from app.extensions import limiter

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # ... código existente ...
```

### 1.2 Configurar Flask-Talisman

```python
# app/__init__.py
from flask_talisman import Talisman

def create_app(config_name='dev'):
    app = Flask(__name__)
    # ... configurações ...
    
    if not app.debug:
        Talisman(app,
            force_https=True,
            strict_transport_security=True,
            session_cookie_secure=True,
            content_security_policy={
                'default-src': "'self'",
                'img-src': ['*', 'data:', 'blob:'],
                'script-src': ["'self'", "'unsafe-inline'"],
                'style-src': ["'self'", "'unsafe-inline'"]
            }
        )
```

### 1.3 Health Check Endpoint

```python
# app/routes/main.py
@main_bp.route('/health')
def health_check():
    try:
        # Verificar DB
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200 if db_status == 'healthy' else 503
```

## 2. OTIMIZAÇÕES DE PERFORMANCE

### 2.1 Adicionar Índices Compostos

```python
# app/models.py
class Transacao(db.Model):
    __tablename__ = 'transacoes'
    # ... campos existentes ...
    
    __table_args__ = (
        Index('idx_trans_status_comprador', 'status', 'comprador_id'),
        Index('idx_trans_status_vendedor', 'status', 'vendedor_id'),
        Index('idx_trans_data_status', 'data_criacao', 'status'),
    )
```

### 2.2 Otimizar Query do Dashboard Admin

```python
# app/routes/admin.py - ANTES
@admin_bp.route('/dashboard')
def dashboard():
    pendentes = Transacao.query.filter_by(status=TransactionStatus.ANALISE).all()
    for t in pendentes:
        print(t.safra.produto.nome)  # N+1 problem!
```

```python
# app/routes/admin.py - DEPOIS
from sqlalchemy.orm import joinedload

@admin_bp.route('/dashboard')
def dashboard():
    pendentes = Transacao.query.options(
        joinedload(Transacao.safra).joinedload(Safra.produto),
        joinedload(Transacao.comprador),
        joinedload(Transacao.vendedor)
    ).filter_by(status=TransactionStatus.ANALISE).all()
```

### 2.3 Implementar Cache Redis

```python
# app/extensions.py
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1',
    'CACHE_DEFAULT_TIMEOUT': 300
})

def setup_extensions(app):
    # ... código existente ...
    cache.init_app(app)
```

```python
# app/routes/mercado.py
from app.extensions import cache

@mercado_bp.route('/produtos')
@cache.cached(timeout=600, key_prefix='produtos_lista')
def listar_produtos():
    produtos = Produto.query.all()
    return render_template('mercado/produtos.html', produtos=produtos)
```

## 3. REFATORAÇÃO - CAMADA DE SERVIÇOS

### 3.1 Criar Serviço de Escrow

```python
# app/services/escrow_service.py
from decimal import Decimal
from app.models import Transacao, Usuario, Notificacao, TransactionStatus
from app.extensions import db

class EscrowService:
    
    @staticmethod
    def validar_pagamento(transacao_id: int, admin_id: int) -> tuple[bool, str]:
        """Valida pagamento e move para escrow"""
        try:
            transacao = Transacao.query.with_for_update().get(transacao_id)
            
            if not transacao:
                return False, "Transação não encontrada"
            
            if transacao.status != TransactionStatus.ANALISE:
                return False, "Transação não está em análise"
            
            transacao.status = TransactionStatus.ESCROW
            transacao.data_pagamento_escrow = datetime.now(timezone.utc)
            
            # Notificar produtor
            notif = Notificacao(
                usuario_id=transacao.vendedor_id,
                mensagem=f"Pagamento validado! Pode enviar a mercadoria (Ref: {transacao.fatura_ref})"
            )
            db.session.add(notif)
            db.session.commit()
            
            return True, "Pagamento validado com sucesso"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erro: {str(e)}"
    
    @staticmethod
    def liberar_pagamento(transacao_id: int) -> tuple[bool, str]:
        """Libera pagamento para o produtor"""
        try:
            transacao = Transacao.query.with_for_update().get(transacao_id)
            
            if transacao.status != TransactionStatus.ENTREGUE:
                return False, "Mercadoria ainda não foi entregue"
            
            vendedor = transacao.vendedor
            vendedor.saldo_disponivel += transacao.valor_liquido_vendedor
            
            transacao.status = TransactionStatus.FINALIZADO
            transacao.data_liquidacao = datetime.now(timezone.utc)
            transacao.transferencia_concluida = True
            
            db.session.commit()
            return True, "Pagamento liberado"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erro: {str(e)}"
```

### 3.2 Usar Serviço nas Rotas

```python
# app/routes/admin.py
from app.services.escrow_service import EscrowService

@admin_bp.route('/validar-pagamento/<int:id>', methods=['POST'])
@login_required
@admin_required
def validar_pagamento(id):
    sucesso, mensagem = EscrowService.validar_pagamento(id, current_user.id)
    
    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')
    
    return redirect(url_for('admin.dashboard'))
```

## 4. MELHORIAS NO DOCKER

### 4.1 Docker Compose com Secrets

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    restart: always
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://agrokongo:${DB_PASSWORD}@db:5432/agrokongo
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./data_storage:/app/data_storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15-alpine
    restart: always
    environment:
      - POSTGRES_DB=agrokongo
      - POSTGRES_USER=agrokongo
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agrokongo"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  postgres_data:
```

### 4.2 Arquivo .env.example

```bash
# .env.example
SECRET_KEY=your-secret-key-here
DB_PASSWORD=your-db-password-here
FLASK_ENV=production
REDIS_URL=redis://redis:6379/0
```

## 5. TESTES DE SEGURANÇA

### 5.1 Teste de CSRF

```python
# tests/security/test_csrf.py
def test_csrf_protection(client):
    """Verifica se CSRF está ativo"""
    response = client.post('/auth/login', data={
        'email': 'test@test.com',
        'senha': '123456'
    })
    assert response.status_code == 400  # Bad Request sem token CSRF
```

### 5.2 Teste de Rate Limiting

```python
# tests/security/test_rate_limit.py
def test_login_rate_limit(client):
    """Verifica rate limiting no login"""
    for i in range(6):
        response = client.post('/auth/login', data={
            'email': 'test@test.com',
            'senha': 'wrong'
        })
    
    assert response.status_code == 429  # Too Many Requests
```

## 6. MONITORING E OBSERVABILIDADE

### 6.1 Prometheus Metrics

```python
# app/monitoring.py
from prometheus_flask_exporter import PrometheusMetrics

def setup_monitoring(app):
    metrics = PrometheusMetrics(app)
    
    # Métricas customizadas
    metrics.info('app_info', 'Application info', version='1.0.0')
    
    @app.route('/metrics')
    def metrics_endpoint():
        return metrics.export()
```

### 6.2 Logging Estruturado

```python
# app/logging_config.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        return json.dumps(log_data)
```

## 7. BACKUP AUTOMATIZADO

### 7.1 Script de Backup

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="agrokongo"

# Backup PostgreSQL
docker exec agrokongo_db pg_dump -U agrokongo $DB_NAME | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup de ficheiros
tar -czf "$BACKUP_DIR/files_$DATE.tar.gz" data_storage/

# Manter apenas últimos 30 dias
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup concluído: $DATE"
```

### 7.2 Cron Job

```bash
# Adicionar ao crontab
0 2 * * * /app/scripts/backup.sh >> /var/log/backup.log 2>&1
```

## 8. DOCUMENTAÇÃO API

### 8.1 Swagger/OpenAPI

```python
# app/__init__.py
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "AgroKongo API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
```

## 9. CORREÇÃO DE BUGS IDENTIFICADOS

### 9.1 Remover Duplicação em extensions.py

```python
# app/extensions.py - CORRIGIDO
def setup_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    
    # Celery
    celery.conf.update(
        broker_url=app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        result_backend=app.config.get('REDIS_URL', 'redis://localhost:6379/0'),
        task_ignore_result=True
    )
    
    # Login Manager
    login_manager.session_protection = "strong"
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Por favor, faça login para aceder a esta página."
    login_manager.login_message_category = "warning"
    
    # Logs
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/agrokongo.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('AgroKongo Startup')
```

### 9.2 Remover Duplicação em __init__.py

```python
# app/__init__.py - CORRIGIDO
@app.context_processor
def inject_globals():
    return {
        'agora': datetime.now(timezone.utc),
        'TStatus': TransactionStatus,
        'now': datetime.now(),
        'timedelta': timedelta
    }
```

### 9.3 Consolidar Campos de Senha

```python
# app/models.py - CORRIGIDO
class Usuario(db.Model, UserMixin):
    # ... outros campos ...
    senha_hash = db.Column(db.String(255), nullable=False)
    # REMOVER: senha = db.Column(db.String(255))
    
    def set_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)
    
    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)
```

## 10. CHECKLIST DE DEPLOY

```markdown
### Antes do Deploy

- [ ] Regenerar requirements.txt limpo
- [ ] Configurar variáveis de ambiente
- [ ] Testar migrations em staging
- [ ] Executar testes de segurança
- [ ] Verificar cobertura de testes (>70%)
- [ ] Revisar logs de erro
- [ ] Configurar backup automatizado
- [ ] Configurar monitoring
- [ ] Documentar API
- [ ] Testar health checks

### Durante o Deploy

- [ ] Fazer backup da DB
- [ ] Executar migrations
- [ ] Verificar health endpoint
- [ ] Testar fluxo crítico (Escrow)
- [ ] Verificar logs em tempo real

### Após o Deploy

- [ ] Monitorar métricas por 24h
- [ ] Verificar alertas
- [ ] Testar performance
- [ ] Validar backup
```
