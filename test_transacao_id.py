"""
Teste rápido para verificar se o ID da transação é gerado corretamente
"""
import sys
from app import create_app
from app.extensions import db
from app.models import Usuario, Provincia, Municipio, Produto, Safra, Transacao
from app.services.compra_service import CompraService
from decimal import Decimal

app = create_app('dev')

with app.app_context():
    # Configurar banco de dados em memória
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
    })
    
    db.create_all()
    
    # Criar estrutura básica
    prov = Provincia(nome='Zaire')
    db.session.add(prov)
    db.session.flush()
    
    mun = Municipio(nome='Mbanza Kongo', provincia_id=prov.id)
    db.session.add(mun)
    db.session.flush()
    
    produtor = Usuario(
        nome="João Produtor",
        telemovel="923000001",
        email="produtor@teste.com",
        tipo="produtor",
        municipio_id=mun.id,
        provincia_id=prov.id,
        perfil_completo=True,
        conta_validada=True
    )
    produtor.senha = "123456"
    db.session.add(produtor)
    
    comprador = Usuario(
        nome="Maria Comprador",
        telemovel="931000001",
        email="comprador@teste.com",
        tipo="comprador",
        municipio_id=mun.id,
        provincia_id=prov.id,
        perfil_completo=True,
        conta_validada=True
    )
    comprador.senha = "123456"
    db.session.add(comprador)
    db.session.commit()
    
    produto = Produto(nome='Mandioca', categoria='Raízes')
    db.session.add(produto)
    db.session.flush()
    
    safra = Safra(
        produtor_id=produtor.id,
        produto_id=produto.id,
        quantidade_disponivel=Decimal('1000.0'),
        preco_por_unidade=Decimal('250.0'),
        status='disponivel'
    )
    db.session.add(safra)
    db.session.commit()
    
    print("=" * 80)
    print("TESTANDO CRIAÇÃO DE TRANSAÇÃO...")
    print("=" * 80)
    
    # Testar criação de transação
    sucesso, transacao, msg = CompraService.iniciar_compra(
        safra_id=safra.id,
        comprador_id=comprador.id,
        quantidade=Decimal('10.0')
    )
    
    print(f"\nSucesso: {sucesso}")
    print(f"Mensagem: {msg}")
    
    if transacao:
        print(f"\n✅ TRANSAÇÃO CRIADA!")
        print(f"   ID: {transacao.id}")
        print(f"   Fatura Ref: {transacao.fatura_ref}")
        print(f"   Status: {transacao.status}")
        print(f"   Valor: {transacao.valor_total_pago}")
        
        if transacao.id is None:
            print("\n❌ ERRO: ID é NONE!")
            sys.exit(1)
        else:
            print("\n✅ SUCESSO: ID foi gerado corretamente!")
    else:
        print(f"\n❌ ERRO: Transação é None")
        sys.exit(1)
    
    print("=" * 80)
