import pytest
from decimal import Decimal
from app.models import Usuario, Produto, Safra, Transacao, TransactionStatus
from app.extensions import db
from app.utils.status_helper import status_to_value

def test_fluxo_completo_compra(client, app):
    """
    Simula um cenário real de negócio (Integration Test):
    1. Criação de Dados (Produtor, Produto, Safra).
    2. Comprador faz login.
    3. Comprador encomenda uma Safra.
    4. Verifica-se se o stock baixou e a transação foi criada na DB.
    """
    
    # 1. SETUP DE DADOS (Arrange)
    safra_id = None
    comprador_id = None
    
    with app.app_context():
        # Criar Produtor
        produtor = Usuario(nome="Produtor Teste", telemovel="920000001", tipo="produtor", conta_validada=True)
        produtor.senha = "123" # Define a senha via setter (hash)
        
        # Criar Comprador
        comprador = Usuario(nome="Comprador Teste", telemovel="930000001", tipo="comprador", conta_validada=True)
        comprador.senha = "123"
        
        db.session.add_all([produtor, comprador])
        db.session.commit()
        
        comprador_id = comprador.id
        
        # Criar Produto
        batata = Produto(nome="Batata Reno", categoria="Tubérculos")
        db.session.add(batata)
        db.session.commit()
        
        # Criar Safra com 100kg a 500kz
        safra = Safra(
            produtor_id=produtor.id,
            produto_id=batata.id,
            quantidade_disponivel=Decimal('100.00'),
            preco_por_unidade=Decimal('500.00'),
            status='disponivel'
        )
        db.session.add(safra)
        db.session.commit()
        
        safra_id = safra.id
    
    # 2. LOGIN DO COMPRADOR
    client.post('/login', data={'telemovel': '930000001', 'senha': '123'}, follow_redirects=True)
    
    # 3. AÇÃO DE COMPRA (Act)
    # Tenta comprar 10kg
    response = client.post(f'/safra/{safra_id}/encomendar', data={'quantidade': '10'}, follow_redirects=True)
    
    # 4. VERIFICAÇÕES (Assert)
    # Verifica resposta HTTP
    assert response.status_code == 200
    # Verifica se a mensagem de sucesso aparece (ajuste conforme a sua flash message real)
    assert b'Reserva' in response.data or b'sucesso' in response.data
    
    with app.app_context():
        # Verificar se a transação foi criada corretamente
        venda = Transacao.query.filter_by(comprador_id=comprador_id).first()
        
        assert venda is not None
        assert venda.quantidade_comprada == Decimal('10.00')
        assert venda.valor_total_pago == Decimal('5000.00') # 10kg * 500kz
        # Comparar valor do enum, nao o enum em si
        assert venda.status == status_to_value(TransactionStatus.PENDENTE) or venda.status == 'pendente'
        
        # Verificar se o stock foi abatido
        safra_atualizada = Safra.query.get(safra_id)
        assert safra_atualizada.quantidade_disponivel == Decimal('90.00') # 100 - 10
        assert safra_atualizada.status == 'disponivel' # Ainda tem stock
