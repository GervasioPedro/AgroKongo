import pytest
from flask import url_for
from decimal import Decimal
from app.models import Transacao, Safra, Produto, Usuario, TransactionStatus
from app.extensions import db

@pytest.fixture
def setup_produtor_data(produtor_user, session):
    # Criar um produto para o produtor
    produto = Produto(nome="Milho", categoria="Grãos", descricao="Milho fresco")
    session.add(produto)
    session.commit()

    # Criar uma safra para o produtor
    safra = Safra(
        produtor_id=produtor_user.id,
        produto_id=produto.id,
        quantidade_disponivel=Decimal('100.000'),
        preco_por_unidade=Decimal('0.50'),
        descricao="Safra de milho 2024",
        status='disponivel'
    )
    session.add(safra)
    session.commit()
    return produtor_user, produto, safra

@pytest.fixture
def setup_transacao_data(produtor_user, comprador_user, setup_produtor_data, session):
    _, _, safra = setup_produtor_data
    # Criar uma transação pendente
    transacao_pendente = Transacao(
        fatura_ref="TRX001",
        safra_id=safra.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('10.000'),
        valor_total_pago=Decimal('5.00'),
        status=TransactionStatus.PENDENTE
    )
    # Criar uma transação em escrow
    transacao_escrow = Transacao(
        fatura_ref="TRX002",
        safra_id=safra.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=Decimal('20.000'),
        valor_total_pago=Decimal('10.00'),
        status=TransactionStatus.ESCROW
    )
    session.add_all([transacao_pendente, transacao_escrow])
    session.commit()
    return transacao_pendente, transacao_escrow

class TestProdutorRoutes:

    # --- Testes para api_criar_safra (Casos de Borda e Validação) ---
    def test_criar_safra_sucesso(self, auth_client, produtor_user, setup_produtor_data):
        produtor_user.conta_validada = True # Simular conta validada
        db.session.commit()
        _, produto, _ = setup_produtor_data
        data = {
            'produto_id': produto.id,
            'quantidade_disponivel': '50.00',
            'preco_por_unidade': '1.25',
            'descricao': 'Nova safra de teste'
        }
        response = auth_client.post(url_for('produtor.api_criar_safra'), data=data)
        assert response.status_code == 201
        assert response.json['ok'] is True
        assert 'Safra criada com sucesso!' in response.json['message']
        
        safra = Safra.query.filter_by(descricao='Nova safra de teste').first()
        assert safra is not None
        assert safra.quantidade_disponivel == Decimal('50.000')

    def test_criar_safra_conta_nao_validada(self, auth_client, produtor_user, setup_produtor_data):
        produtor_user.conta_validada = False # Simular conta não validada
        db.session.commit()
        _, produto, _ = setup_produtor_data
        data = {
            'produto_id': produto.id,
            'quantidade_disponivel': '50.00',
            'preco_por_unidade': '1.25',
            'descricao': 'Nova safra de teste'
        }
        response = auth_client.post(url_for('produtor.api_criar_safra'), data=data)
        assert response.status_code == 403
        assert response.json['ok'] is False
        assert 'A sua conta precisa de ser validada' in response.json['message']

    def test_criar_safra_dados_invalidos(self, auth_client, produtor_user, setup_produtor_data):
        produtor_user.conta_validada = True
        db.session.commit()
        # Testar quantidade negativa
        data = {
            'produto_id': 999, # Produto inexistente
            'quantidade_disponivel': '-10.00',
            'preco_por_unidade': 'abc', # Preço inválido
            'descricao': ''
        }
        response = auth_client.post(url_for('produtor.api_criar_safra'), data=data)
        # Espera-se 400 ou 500 dependendo da validação
        assert response.status_code in [400, 500] 
        assert response.json['ok'] is False

    # --- Testes para api_eliminar_safra (Casos de Borda) ---
    def test_eliminar_safra_com_transacoes_ativas(self, auth_client, produtor_user, setup_produtor_data, setup_transacao_data):
        produtor_user.conta_validada = True
        db.session.commit()
        _, _, safra = setup_produtor_data
        transacao_pendente, _ = setup_transacao_data
        
        response = auth_client.delete(url_for('produtor.api_eliminar_safra', id=safra.id))
        assert response.status_code == 409
        assert response.json['ok'] is False
        assert 'Não é possível eliminar uma safra com pedidos ativos' in response.json['message']

    def test_eliminar_safra_sucesso(self, auth_client, produtor_user, setup_produtor_data, session):
        produtor_user.conta_validada = True
        db.session.commit()
        _, _, safra = setup_produtor_data
        # Garantir que não há transações ativas para esta safra
        Transacao.query.filter_by(safra_id=safra.id).delete()
        session.commit()

        response = auth_client.delete(url_for('produtor.api_eliminar_safra', id=safra.id))
        assert response.status_code == 200
        assert response.json['ok'] is True
        assert 'Safra eliminada com sucesso.' in response.json['message']
        assert Safra.query.get(safra.id) is None

    # --- Testes para api_aceitar_reserva / api_recusar_reserva (Casos de Borda) ---
    def test_aceitar_reserva_estado_invalido(self, auth_client, produtor_user, setup_transacao_data):
        produtor_user.conta_validada = True
        db.session.commit()
        _, transacao_escrow = setup_transacao_data # Transação já em ESCROW
        response = auth_client.post(url_for('produtor.api_aceitar_reserva', trans_id=transacao_escrow.id))
        assert response.status_code == 409
        assert response.json['ok'] is False
        assert 'Esta reserva já foi processada.' in response.json['message']

    def test_recusar_reserva_stock_reposto(self, auth_client, produtor_user, setup_transacao_data, session):
        produtor_user.conta_validada = True
        db.session.commit()
        transacao_pendente, _ = setup_transacao_data
        safra_original_qty = transacao_pendente.safra.quantidade_disponivel
        
        response = auth_client.post(url_for('produtor.api_recusar_reserva', trans_id=transacao_pendente.id))
        assert response.status_code == 200
        assert response.json['ok'] is True
        assert 'Reserva recusada e stock reposto.' in response.json['message']
        
        session.refresh(transacao_pendente.safra)
        assert transacao_pendente.safra.quantidade_disponivel == safra_original_qty + transacao_pendente.quantidade_comprada
        assert transacao_pendente.status == TransactionStatus.CANCELADO

    # --- Testes para api_confirmar_envio (Casos de Borda) ---
    def test_confirmar_envio_estado_invalido(self, auth_client, produtor_user, setup_transacao_data):
        produtor_user.conta_validada = True
        db.session.commit()
        transacao_pendente, _ = setup_transacao_data # Transação em PENDENTE
        response = auth_client.post(url_for('produtor.api_confirmar_envio', id=transacao_pendente.id))
        assert response.status_code == 409
        assert response.json['ok'] is False
        assert 'Ação inválida. O pagamento deve ser confirmado primeiro.' in response.json['message']

    # --- Testes de Autorização ---
    def test_produtor_required_comprador_acesso(self, auth_client, comprador_user):
        response = auth_client.get(url_for('produtor.api_dashboard_produtor'))
        assert response.status_code == 403
        assert response.json['ok'] is False
        assert 'Acesso restrito a produtores.' in response.json['message']

    def test_produtor_required_nao_autenticado_acesso(self, client):
        response = client.get(url_for('produtor.api_dashboard_produtor'))
        # O Flask-Login UnauthorizedHandler em app/extensions.py deve retornar JSON 401 para /api/*
        assert response.status_code == 401
        assert response.json['ok'] is False
        assert 'Nao autenticado.' in response.json['message']
