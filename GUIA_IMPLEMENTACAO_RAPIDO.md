# 🚀 GUIA RÁPIDO DE IMPLEMENTAÇÃO AGROKONGO 2026

**Data:** Março 2026  
**Objetivo:** Implementar melhorias críticas em 8 semanas  
**Status:** APROVADO PARA IMPLEMENTAÇÃO IMEDIATA

---

## 📋 SEMANA 1: ÍNDICES E TESTES UNITÁRIOS

### Dia 1-2: Índices de Database

#### Passo 1: Criar Migration
```bash
# Ativar ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # Windows

# Criar migration de índices
flask db migrate -m "Add strategic indexes for performance"
```

#### Passo 2: Editar Migration (versions/xxxx_add_strategic_indexes.py)
```python
def upgrade():
    # Transações
    op.create_index('idx_trans_fatura_ref_busca', 'transacoes', ['fatura_ref'])
    op.create_index('idx_trans_data_criacao_status', 'transacoes', ['data_criacao', 'status'])
    
    # Safras
    op.create_index('idx_safra_produto_status', 'safras', ['produto_id', 'status'])
    op.create_index('idx_safra_data_criacao', 'safras', ['data_criacao'])
    
    # Usuários
    op.create_index('idx_usuario_conta_validada_tipo', 'usuarios', ['conta_validada', 'tipo'])
    op.create_index('idx_usuario_data_cadastro', 'usuarios', ['data_cadastro'])
    
    # Notificações
    op.create_index('idx_notificacao_usuario_lida', 'notificacoes', ['usuario_id', 'lida'])
    op.create_index('idx_notificacao_data', 'notificacoes', ['data_criacao'])

def downgrade():
    op.drop_index('idx_notificacao_data', table_name='notificacoes')
    op.drop_index('idx_notificacao_usuario_lida', table_name='notificacoes')
    op.drop_index('idx_usuario_data_cadastro', table_name='usuarios')
    op.drop_index('idx_usuario_conta_validada_tipo', table_name='usuarios')
    op.drop_index('idx_safra_data_criacao', table_name='safras')
    op.drop_index('idx_safra_produto_status', table_name='safras')
    op.drop_index('idx_trans_data_criacao_status', table_name='transacoes')
    op.drop_index('idx_trans_fatura_ref_busca', table_name='transacoes')
```

#### Passo 3: Aplicar Migration
```bash
# Ambiente de desenvolvimento
flask db upgrade

# Validar performance
python scripts/test_query_performance.py
```

#### Passo 4: Validar Performance
```python
# scripts/test_query_performance.py
import time
from app import create_app
from app.extensions import db
from app.models import Transacao, Safra, Usuario

app = create_app('dev')

with app.app_context():
    # Query 1: Transações por status
    start = time.time()
    transacoes = Transacao.query.filter_by(status='pendente').all()
    end = time.time()
    print(f"Query 1 (transações por status): {end - start:.3f}s")
    
    # Query 2: Safras por produto
    start = time.time()
    safras = Safra.query.filter_by(produto_id=1, ativa=True).all()
    end = time.time()
    print(f"Query 2 (safras por produto): {end - start:.3f}s")
    
    # Query 3: Usuários validados
    start = time.time()
    usuarios = Usuario.query.filter_by(conta_validada=True, tipo='produtor').all()
    end = time.time()
    print(f"Query 3 (usuários validados): {end - start:.3f}s")
```

**Resultado Esperado:** Queries 50x mais rápidas

---

### Dia 3-7: Testes Unitários de Services

#### Passo 1: Configurar Ambiente de Testes
```bash
# Instalar dependências de teste
pip install pytest pytest-cov pytest-mock freezegun

# Verificar configuração
pytest --version
```

#### Passo 2: Criar Testes do EscrowService
```python
# tests/unit/test_escrow_service.py
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from app.services.escrow_service import EscrowService
from app.models import Transacao, TransactionStatus, HistoricoStatus

class TestEscrowService:
    
    def test_validar_pagamento_sucesso(self, session, transacao_em_analise, admin):
        """Valida pagamento e move para escrow com sucesso"""
        sucesso, mensagem = EscrowService.validar_pagamento(
            transacao_id=transacao_em_analise.id,
            admin_id=admin.id
        )
        
        assert sucesso is True
        assert mensagem == "Pagamento validado com sucesso"
        assert transacao_em_analise.status == TransactionStatus.ESCROW
        assert transacao_em_analise.data_pagamento_escrow is not None
    
    def test_validar_pagamento_transacao_nao_existe(self, session, admin):
        """Falha ao validar pagamento de transação inexistente"""
        sucesso, mensagem = EscrowService.validar_pagamento(
            transacao_id=999999,
            admin_id=admin.id
        )
        
        assert sucesso is False
        assert "não encontrada" in mensagem
    
    def test_liberar_pagamento_entrega_confirmada(self, session, transacao_entregue):
        """Libera pagamento após confirmação de entrega"""
        saldo_anterior = transacao_entregue.vendedor.saldo_disponivel
        
        sucesso, mensagem = EscrowService.liberar_pagamento(
            transacao_id=transacao_entregue.id
        )
        
        assert sucesso is True
        assert transacao_entregue.status == TransactionStatus.FINALIZADO
        assert transacao_entregue.transferencia_concluida is True
        assert transacao_entregue.vendedor.saldo_disponivel > saldo_anterior
    
    def test_calcular_valores_comissao_5_porcento(self):
        """Calcula comissão de 5% corretamente"""
        valor_total = Decimal('1000.00')
        
        resultado = EscrowService.calcular_valores(valor_total)
        
        assert resultado['comissao'] == Decimal('50.00')
        assert resultado['valor_liquido'] == Decimal('950.00')
```

#### Passo 3: Criar Fixtures
```python
# tests/conftest.py (adicionar)
@pytest.fixture
def admin(session):
    """Usuário administrador para testes"""
    admin = Usuario(
        nome="Admin Test",
        telemovel="911111111",
        email="admin@test.com",
        senha="admin123",
        tipo="admin",
        conta_validada=True
    )
    session.add(admin)
    session.commit()
    return admin

@pytest.fixture
def transacao_em_analise(session, comprador_user, vendedor_user, safra_ativa):
    """Transação em status de análise para testes"""
    from app.models.auditoria import ConfiguracaoSistema
    
    taxa = ConfiguracaoSistema.obter_valor_decimal('TAXA_PLATAFORMA', padrao=Decimal('0.05'))
    
    transacao = Transacao(
        fatura_ref="REF20260001",
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=vendedor_user.id,
        quantidade_comprada=Decimal('100.00'),
        valor_total_pago=Decimal('15000.00'),
        status=TransactionStatus.ANALISE
    )
    transacao.recalcular_financeiro(taxa_plataforma=taxa)
    
    session.add(transacao)
    session.commit()
    return transacao

@pytest.fixture
def transacao_entregue(session, comprador_user, vendedor_user, safra_ativa):
    """Transação em status entregue para testes"""
    from app.models.auditoria import ConfiguracaoSistema
    
    taxa = ConfiguracaoSistema.obter_valor_decimal('TAXA_PLATAFORMA', padrao=Decimal('0.05'))
    
    transacao = Transacao(
        fatura_ref="REF20260002",
        safra_id=safra_ativa.id,
        comprador_id=comprador_user.id,
        vendedor_id=vendedor_user.id,
        quantidade_comprada=Decimal('100.00'),
        valor_total_pago=Decimal('15000.00'),
        status=TransactionStatus.ENTREGUE,
        data_entrega=datetime.now(timezone.utc)
    )
    transacao.recalcular_financeiro(taxa_plataforma=taxa)
    
    session.add(transacao)
    session.commit()
    return transacao
```

#### Passo 4: Executar e Validar
```bash
# Rodar testes do EscrowService
pytest tests/unit/test_escrow_service.py -v

# Gerar relatório de cobertura
pytest tests/unit/test_escrow_service.py --cov=app.services.escrow_service --cov-report=html

# Abrir relatório
start htmlcov/index.html  # Windows
```

**Meta:** 90% de cobertura no EscrowService

---

## 📋 SEMANA 2: NOTIFICACAO SERVICE E OTP

### Dia 1-3: Testes do NotificacaoService

#### Criar Arquivo de Testes
```python
# tests/unit/test_notificacao_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.notificacao_service import NotificacaoService
from app.models import Notificacao

class TestNotificacaoService:
    
    @patch('app.services.notificacao.send_email')
    def test_enviar_notificacao_email(self, mock_send_email, session, usuario):
        """Envia notificação por email com sucesso"""
        assunto = "Pagamento Validado"
        corpo = "Seu pagamento foi validado"
        
        with patch.object(NotificacaoService, '_criar_notificacao_bd') as mock_bd:
            sucesso = NotificacaoService.enviar_email(
                destinatario=usuario.email,
                assunto=assunto,
                corpo=corpo
            )
            
            assert sucesso is True
            mock_send_email.assert_called_once()
            mock_bd.assert_called_once()
    
    @patch('app.services.notificacao.send_push_notification')
    def test_enviar_notificacao_push(self, mock_send_push, session, usuario):
        """Envia notificação push com sucesso"""
        mensagem = "Nova transação criada"
        
        sucesso = NotificacaoService.enviar_push(
            usuario_id=usuario.id,
            mensagem=mensagem
        )
        
        assert sucesso is True
        mock_send_push.assert_called_once()
    
    def test_criar_notificacao_database(self, session, usuario):
        """Cria notificação no banco de dados"""
        notificacao = NotificacaoService.criar_notificacao(
            usuario_id=usuario.id,
            mensagem="Teste de notificação",
            link="/dashboard"
        )
        
        assert notificacao.id is not None
        assert notificacao.lida is False
        assert notificacao.usuario_id == usuario.id
```

---

### Dia 4-7: Testes do OTPService

#### Criar Arquivo de Testes
```python
# tests/unit/test_otp_service.py
import pytest
from datetime import timedelta
from freezegun import freeze_time
from app.services.otp_service import OTPService

class TestOTPService:
    
    def test_gerar_otp_valido(self, session, usuario):
        """Gera OTP válido por 5 minutos"""
        otp_codigo = OTPService.gerar_otp(usuario)
        
        assert otp_codigo is not None
        assert len(otp_codigo) == 6
        assert otp_codigo.isdigit()
    
    def test_verificar_otp_sucesso(self, session, usuario):
        """Verifica OTP com sucesso"""
        otp_codigo = OTPService.gerar_otp(usuario)
        
        sucesso = OTPService.verificar_otp(
            usuario=usuario,
            otp_codigo=otp_codigo
        )
        
        assert sucesso is True
    
    @freeze_time("2026-03-06 12:00:00")
    def test_verificar_otp_expirado(self, session, usuario, freezer):
        """Falha ao verificar OTP expirado (5 min)"""
        otp_codigo = OTPService.gerar_otp(usuario)
        
        # Avançar 6 minutos
        freezer.move_to("2026-03-06 12:06:00")
        
        sucesso = OTPService.verificar_otp(
            usuario=usuario,
            otp_codigo=otp_codigo
        )
        
        assert sucesso is False
    
    def test_verificar_otp_reutilizacao(self, session, usuario):
        """Não permite reutilizar OTP"""
        otp_codigo = OTPService.gerar_otp(usuario)
        
        # Primeira verificação
        OTPService.verificar_otp(usuario, otp_codigo)
        
        # Segunda verificação deve falhar
        sucesso = OTPService.verificar_otp(usuario, otp_codigo)
        
        assert sucesso is False
    
    def test_limpar_otps_expirados(self, session, usuario, freezer):
        """Limpa OTPs expirados do banco"""
        # Criar OTP expirado
        freezer.move_to("2026-03-06 11:00:00")
        OTPService.gerar_otp(usuario)
        
        # Avançar 1 hora
        freezer.move_to("2026-03-06 12:00:00")
        
        # Limpar expirados
        OTPService.limpar_otps_expirados()
        
        # Verificar se foi removido
        from app.models import OTP
        otps = OTP.query.filter_by(usuario_id=usuario.id).all()
        assert len(otps) == 0
```

---

## 📋 SEMANA 3-4: TESTES DE INTEGRAÇÃO

### Dia 1-7: API Endpoints

#### Testes de Auth
```python
# tests/integration/test_auth_api.py
import pytest

class TestAuthAPI:
    
    def test_login_sucesso(self, client, usuario):
        """Login com credenciais válidas"""
        response = client.post('/api/auth/login', json={
            'email': usuario.email,
            'senha': 'senha123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'token' in data['data']
    
    def test_login_senha_invalida(self, client, usuario):
        """Falha com senha inválida"""
        response = client.post('/api/auth/login', json={
            'email': usuario.email,
            'senha': 'senha_errada'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_registro_produtor_sucesso(self, client, provincia, municipio):
        """Registro de produtor com sucesso"""
        payload = {
            'nome': 'Produtor Novo',
            'telemovel': '933445566',
            'email': 'novo@produtor.com',
            'senha': 'senha123',
            'tipo': 'produtor',
            'provincia_id': provincia.id,
            'municipio_id': municipio.id
        }
        
        response = client.post('/api/auth/registro', json=payload)
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'usuario_id' in data['data']
```

---

## 📋 SEMANA 5-6: TESTES E2E

### Fluxo Completo de Compra

```python
# tests/e2e/test_fluxo_compra.py
class TestFluxoCompra:
    
    def test_jornada_completa_comprador(self, client, session):
        """Comprador completa jornada desde cadastro até confirmação"""
        
        # 1. Cadastro
        registro_response = client.post('/api/auth/registro', json={
            'nome': 'João Comprador',
            'telemovel': '944556677',
            'email': 'joao@comprador.com',
            'senha': 'senha123',
            'tipo': 'comprador'
        })
        assert registro_response.status_code == 201
        
        # 2. Login
        login_response = client.post('/api/auth/login', json={
            'email': 'joao@comprador.com',
            'senha': 'senha123'
        })
        assert login_response.status_code == 200
        token = login_response.get_json()['data']['token']
        
        headers = {'Authorization': f'Bearer {token}'}
        
        # 3. Listar produtos
        produtos_response = client.get('/api/v1/produtos', headers=headers)
        assert produtos_response.status_code == 200
        
        # 4. Criar transação
        transacao_response = client.post('/api/v1/transacoes', json={
            'safra_id': 1,
            'quantidade': 100
        }, headers=headers)
        assert transacao_response.status_code == 201
        
        # 5. Confirmar recebimento
        confirmacao_response = client.post(
            f'/api/v1/transacoes/{transacao_id}/confirmar-entrega',
            headers=headers
        )
        assert confirmacao_response.status_code == 200
```

---

## 📋 COMANDOS ÚTEIS

### Executar Testes
```bash
# Testes rápidos (unitários)
pytest tests/unit/ -v --tb=short

# Suite completa
pytest -v --tb=short --cov=app

# Com relatório HTML
pytest --html=reports/test_report.html

# Testes específicos
pytest tests/unit/test_escrow_service.py::TestEscrowService::test_validar_pagamento_sucesso -v
```

### Validar Performance
```bash
# Testar queries
python scripts/test_query_performance.py

# Benchmark
pytest tests/performance/ -v
```

---

## ✅ CHECKLIST DIÁRIO

### Início do Dia
```markdown
[ ] Git pull (últimas mudanças)
[ ] Revisar tarefas do dia
[ ] Verificar testes falhando
```

### Fim do Dia
```markdown
[ ] Commit das mudanças
[ ] Push para branch
[ ] Atualizar documentação
[ ] Planejar próximo dia
```

---

## 📊 ACOMPANHAMENTO

### Métricas Diárias
```
Dia 1:  Cobertura 65% → 68% (+3%)
Dia 2:  Cobertura 68% → 70% (+2%)
Dia 3:  Cobertura 70% → 73% (+3%)
...
Dia 40: Cobertura 82% → 85% (+3%) ✅ META ATINGIDA
```

---

**Próxima Ação:** Iniciar Semana 1 imediatamente!
