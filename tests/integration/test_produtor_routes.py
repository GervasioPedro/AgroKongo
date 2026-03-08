import pytest
from flask import url_for
from decimal import Decimal
from app.models import Safra, Transacao, TransactionStatus

# Fixtures já definidas no conftest.py (setup_produtor_data, etc)
# Vamos usar as do conftest para evitar duplicação e erros de integridade

class TestProdutorRoutes:

    def test_criar_safra_sucesso(self, auth_client, produtor_user, produto):
        produtor_user.conta_validada = True
        # Não precisamos de commit aqui porque a fixture session já trata disso
        
        data = {
            'produto_id': produto.id,
            'quantidade_disponivel': '50.00',
            'preco_por_unidade': '1.25',
            'descricao': 'Nova safra de teste'
        }
        response = auth_client.post(url_for('produtor.api_criar_safra'), data=data)
        assert response.status_code == 201
        assert response.json['ok'] is True

    def test_produtor_required_nao_autenticado_acesso(self, client, app):
        # CORREÇÃO: Usar contexto de requisição
        with app.test_request_context():
            url = url_for('produtor.api_dashboard_produtor')
        
        response = client.get(url)
        assert response.status_code == 401
