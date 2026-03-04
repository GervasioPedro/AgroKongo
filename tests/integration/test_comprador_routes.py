import pytest
from flask import url_for
from decimal import Decimal
from app.models import Transacao, Safra, Produto, Usuario, Avaliacao, TransactionStatus
from app.extensions import db

# Reutilizando fixtures de 'test_produtor_routes.py' se estiverem no conftest.py
# Por agora, vamos assumir que estão disponíveis ou redefini-los aqui.

@pytest.fixture
def setup_comprador_transacoes(produtor_user, comprador_user, session):
    produto = Produto.query.first()
    if not produto:
        produto = Produto(nome="Café", categoria="Grãos")
        session.add(produto)
        session.commit()

    safra = Safra.query.filter_by(produtor_id=produtor_user.id).first()
    if not safra:
        safra = Safra(produtor_id=produtor_user.id, produto_id=produto.id, quantidade_disponivel=100, preco_por_unidade=10)
        session.add(safra)
        session.commit()

    # Transação em estado 'ENVIADO' para testar confirmação de recebimento
    trans_enviada = Transacao(
        uuid="a1b2c3d4-e5f6-7890-1234-567890abcdef",
        fatura_ref="TRX_ENVIADO_01",
        safra_id=safra.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=5,
        valor_total_pago=50,
        status=TransactionStatus.ENVIADO
    )

    # Transação em estado 'ENTREGUE' para testar avaliação
    trans_entregue = Transacao(
        fatura_ref="TRX_ENTREGUE_01",
        safra_id=safra.id,
        comprador_id=comprador_user.id,
        vendedor_id=produtor_user.id,
        quantidade_comprada=2,
        valor_total_pago=20,
        status=TransactionStatus.ENTREGUE
    )
    
    session.add_all([trans_enviada, trans_entregue])
    session.commit()
    return trans_enviada, trans_entregue

class TestCompradorRoutes:

    # --- Testes para confirmar_recebimento ---
    def test_confirmar_recebimento_sucesso(self, auth_comprador_client, setup_comprador_transacoes, mocker):
        # Mock da task Celery para não a executar de verdade
        mock_task = mocker.patch('app.routes.comprador.processar_liquidacao.delay')
        trans_enviada, _ = setup_comprador_transacoes

        response = auth_comprador_client.post(
            url_for('comprador.confirmar_recebimento', trans_uuid=trans_enviada.uuid)
        )
        
        assert response.status_code == 302 # Redirect para o dashboard
        
        # Verificar se a task foi chamada
        mock_task.assert_called_once_with(trans_enviada.id)
        
        # Verificar o estado da transação na DB
        db.session.refresh(trans_enviada)
        assert trans_enviada.status == TransactionStatus.ENTREGUE
        assert trans_enviada.data_entrega is not None

    def test_confirmar_recebimento_status_invalido(self, auth_comprador_client, setup_comprador_transacoes):
        _, trans_entregue = setup_comprador_transacoes # Já está 'ENTREGUE'
        
        response = auth_comprador_client.post(
            url_for('comprador.confirmar_recebimento', trans_uuid=trans_entregue.uuid)
        )
        assert response.status_code == 302
        # Verificar a flash message (requer configuração extra no client de teste)

    def test_confirmar_recebimento_outro_utilizador(self, auth_client, setup_comprador_transacoes):
        # auth_client está autenticado como produtor_user por defeito
        trans_enviada, _ = setup_comprador_transacoes
        
        response = auth_client.post(
            url_for('comprador.confirmar_recebimento', trans_uuid=trans_enviada.uuid)
        )
        assert response.status_code == 403 # Abort(403)

    # --- Testes para api_avaliar_venda ---
    def test_api_avaliar_venda_sucesso(self, auth_comprador_client, setup_comprador_transacoes):
        _, trans_entregue = setup_comprador_transacoes
        data = {'estrelas': 5, 'comentario': 'Excelente produto!'}
        
        response = auth_comprador_client.post(
            url_for('comprador.api_avaliar_venda', id=trans_entregue.id),
            json=data
        )
        
        assert response.status_code == 200
        assert response.json['ok'] is True
        assert 'Obrigado pela sua avaliação!' in response.json['message']
        
        avaliacao = Avaliacao.query.filter_by(transacao_id=trans_entregue.id).first()
        assert avaliacao is not None
        assert avaliacao.estrelas == 5
        assert avaliacao.comentario == 'Excelente produto!'

    def test_api_avaliar_venda_duplicada(self, auth_comprador_client, setup_comprador_transacoes):
        _, trans_entregue = setup_comprador_transacoes
        
        # Primeira avaliação
        Avaliacao.query.delete() # Limpar avaliações anteriores
        db.session.commit()
        auth_comprador_client.post(
            url_for('comprador.api_avaliar_venda', id=trans_entregue.id),
            json={'estrelas': 4}
        )
        
        # Tentar avaliar novamente
        response = auth_comprador_client.post(
            url_for('comprador.api_avaliar_venda', id=trans_entregue.id),
            json={'estrelas': 5}
        )
        
        assert response.status_code == 409
        assert response.json['ok'] is False
        assert 'Esta transação já foi avaliada.' in response.json['message']

    def test_api_avaliar_venda_dados_invalidos(self, auth_comprador_client, setup_comprador_transacoes):
        _, trans_entregue = setup_comprador_transacoes
        
        # Estrelas fora do range
        response = auth_comprador_client.post(
            url_for('comprador.api_avaliar_venda', id=trans_entregue.id),
            json={'estrelas': 6, 'comentario': 'Muitas estrelas'}
        )
        assert response.status_code == 400
        assert 'A avaliação em estrelas (1 a 5) é obrigatória.' in response.json['message']
        
        # Sem estrelas
        response = auth_comprador_client.post(
            url_for('comprador.api_avaliar_venda', id=trans_entregue.id),
            json={'comentario': 'Sem estrelas'}
        )
        assert response.status_code == 400

    # --- Testes para api_abrir_disputa ---
    def test_api_abrir_disputa_sucesso(self, auth_comprador_client, setup_comprador_transacoes):
        trans_enviada, _ = setup_comprador_transacoes
        
        response = auth_comprador_client.post(
            url_for('comprador.api_abrir_disputa', id=trans_enviada.id)
        )
        
        assert response.status_code == 200
        assert response.json['ok'] is True
        assert 'Disputa aberta.' in response.json['message']
        
        db.session.refresh(trans_enviada)
        assert trans_enviada.status == TransactionStatus.DISPUTA

    def test_api_abrir_disputa_status_invalido(self, auth_comprador_client, setup_comprador_transacoes):
        _, trans_entregue = setup_comprador_transacoes
        trans_entregue.status = TransactionStatus.FINALIZADO # Marcar como finalizada
        db.session.commit()
        
        response = auth_comprador_client.post(
            url_for('comprador.api_abrir_disputa', id=trans_entregue.id)
        )
        
        assert response.status_code == 409
        assert 'Não é possível abrir disputa' in response.json['message']

    def test_api_abrir_disputa_duplicada(self, auth_comprador_client, setup_comprador_transacoes):
        trans_enviada, _ = setup_comprador_transacoes
        trans_enviada.status = TransactionStatus.DISPUTA # Já está em disputa
        db.session.commit()
        
        response = auth_comprador_client.post(
            url_for('comprador.api_abrir_disputa', id=trans_enviada.id)
        )
        
        assert response.status_code == 409
        assert 'Já existe uma disputa aberta.' in response.json['message']
