"""
Script de Seed - Dados Iniciais para Desenvolvimento
Cria dados básicos para testes locais
"""
import os
import sys
from decimal import Decimal

# Adicionar root do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import (
    Usuario, Provincia, Municipio, Produto, Safra, 
    Carteira, ConfiguracaoSistema
)
from datetime import datetime, timezone


def criar_provincias_municipios():
    """Cria províncias e municípios de Angola"""
    print("📍 Criando províncias e municípios...")
    
    dados_angola = {
        'Luanda': ['Belas', 'Cacuaco', 'Viana', 'Íngua', 'Talatona'],
        'Benguela': ['Lobito', 'Catumbela', 'Baía Farta'],
        'Huíla': ['Lubango', 'Humpata', 'Chibia'],
        'Cabinda': ['Cabinda', 'Cacongo', 'Buco-Zau']
    }
    
    for provincia_nome, municipios in dados_angola.items():
        provincia = Provincia.query.filter_by(nome=provincia_nome).first()
        
        if not provincia:
            provincia = Provincia(nome=provincia_nome)
            db.session.add(provincia)
            print(f"  ✓ Criada província: {provincia_nome}")
        
        for municipio_nome in municipios:
            municipio = Municipio.query.filter_by(
                nome=municipio_nome,
                provincia_id=provincia.id
            ).first()
            
            if not municipio:
                municipio = Municipio(nome=municipio_nome, provincia=provincia)
                db.session.add(municipio)
    
    db.session.commit()
    print("  ✅ Províncias e municípios criados!\n")


def criar_administradores():
    """Cria usuários administradores"""
    print("👤 Criando administradores...")
    
    admin = Usuario.query.filter_by(email='admin@agrokongo.ao').first()
    
    if not admin:
        admin = Usuario(
            nome='Administrador Sistema',
            email='admin@agrokongo.ao',
            telemovel='923456789',
            tipo='admin',
            conta_validada=True,
            perfil_completo=True,
            ativo=True
        )
        admin.set_senha('Admin123!')
        db.session.add(admin)
        print("  ✓ Admin criado: admin@agrokongo.ao / Admin123!")
    
    db.session.commit()
    print("  ✅ Administradores criados!\n")


def criar_usuarios_exemplo():
    """Cria usuários de exemplo para testes"""
    print("👥 Criando usuários de exemplo...")
    
    # Produtor 1
    produtor1 = Usuario.query.filter_by(email='joao.silva@example.ao').first()
    if not produtor1:
        produtor1 = Usuario(
            nome='João Silva',
            email='joao.silva@example.ao',
            telemovel='923456789',
            tipo='produtor',
            nif='123456789',
            iban='AO06.0000.0000.0000.0000.0',
            provincia_id=1,  # Luanda
            municipio_id=1,  # Belas
            conta_validada=True,
            perfil_completo=True,
            saldo_disponivel=Decimal('5000.00'),
            vendas_concluidas=15
        )
        produtor1.set_senha('Produtor123!')
        db.session.add(produtor1)
        print("  ✓ Produtor: joao.silva@example.ao / Produtor123!")
    
    # Comprador 1
    comprador1 = Usuario.query.filter_by(email='maria.santos@example.ao').first()
    if not comprador1:
        comprador1 = Usuario(
            nome='Maria Santos',
            email='maria.santos@example.ao',
            telemovel='933456789',
            tipo='comprador',
            nif='987654321',
            provincia_id=1,
            municipio_id=2,  # Cacuaco
            conta_validada=True,
            perfil_completo=True,
            saldo_disponivel=Decimal('10000.00'),
            limite_credito=Decimal('5000.00')
        )
        comprador1.set_senha('Comprador123!')
        db.session.add(comprador1)
        print("  ✓ Comprador: maria.santos@example.ao / Comprador123!")
    
    db.session.commit()
    print("  ✅ Usuários de exemplo criados!\n")


def criar_produtos():
    """Cria produtos agrícolas básicos"""
    print("🌽 Criando produtos...")
    
    produtos = [
        {'nome': 'Milho', 'categoria': 'Cereais', 'descricao': 'Milho branco angolano'},
        {'nome': 'Feijão', 'categoria': 'Leguminosas', 'descricao': 'Feijão frade'},
        {'nome': 'Arroz', 'categoria': 'Cereais', 'descricao': 'Arroz irrigado'},
        {'nome': 'Mandioca', 'categoria': 'Tubérculos', 'descricao': 'Mandioca fresca'},
        {'nome': 'Batata Doce', 'categoria': 'Tubérculos', 'descricao': 'Batata doce laranja'},
        {'nome': 'Tomate', 'categoria': 'Hortícolas', 'descricao': 'Tomate maduro'},
        {'nome': 'Cebola', 'categoria': 'Hortícolas', 'descricao': 'Cebola roxa'},
        {'nome': 'Alho', 'categoria': 'Hortícolas', 'descricao': 'Alho fresco'},
    ]
    
    for produto_data in produtos:
        produto = Produto.query.filter_by(
            nome=produto_data['nome']
        ).first()
        
        if not produto:
            produto = Produto(**produto_data)
            db.session.add(produto)
            print(f"  ✓ Produto: {produto_data['nome']}")
    
    db.session.commit()
    print("  ✅ Produtos criados!\n")


def criar_safras_exemplo():
    """Cria safras de exemplo para produtores"""
    print("🌾 Criando safras de exemplo...")
    
    produtor = Usuario.query.filter_by(
        email='joao.silva@example.ao'
    ).first()
    
    if not produtor:
        print("  ⚠️  Produtor não encontrado, pulando safras...")
        return
    
    produtos = Produto.query.all()
    
    if not produtos:
        print("  ⚠️  Nenhum produto encontrado, pulando safras...")
        return
    
    # Criar 3 safras de exemplo
    safras_data = [
        {
            'produto': 'Milho',
            'quantidade': Decimal('1000.000'),
            'preco': Decimal('45.00'),
            'localizacao': 'Belas, Luanda'
        },
        {
            'produto': 'Feijão',
            'quantidade': Decimal('500.000'),
            'preco': Decimal('80.00'),
            'localizacao': 'Viana, Luanda'
        },
        {
            'produto': 'Batata Doce',
            'quantidade': Decimal('750.000'),
            'preco': Decimal('35.00'),
            'localizacao': 'Cacuaco, Luanda'
        }
    ]
    
    for safra_data in safras_data:
        produto = next((p for p in produtos if p.nome == safra_data['produto']), None)
        
        if produto:
            safra = Safra.query.filter_by(
                produtor_id=produtor.id,
                produto_id=produto.id,
                localizacao=safra_data['localizacao']
            ).first()
            
            if not safra:
                safra = Safra(
                    produtor=produtor,
                    produto=produto,
                    quantidade_disponivel=safra_data['quantidade'],
                    preco_por_unidade=safra_data['preco'],
                    descricao=f"{safra_data['produto']} de alta qualidade",
                    localizacao=safra_data['localizacao'],
                    status='disponivel'
                )
                db.session.add(safra)
                print(f"  ✓ Safra: {safra_data['quantidade']}kg de {safra_data['produto']}")
    
    db.session.commit()
    print("  ✅ Safras criadas!\n")


def criar_configuracoes_sistema():
    """Cria configurações padrão do sistema"""
    print("⚙️  Criando configurações do sistema...")
    
    configs = [
        {
            'chave': 'TAXA_PLATAFORMA',
            'valor': '0.10',
            'descricao': 'Taxa da plataforma (10%) para transações'
        },
        {
            'chave': 'VALOR_MINIMO_TRANSACAO',
            'valor': '100.00',
            'descricao': 'Valor mínimo para transação em Kz'
        },
        {
            'chave': 'VALOR_MAXIMO_TRANSACAO',
            'valor': '1000000.00',
            'descricao': 'Valor máximo para transação em Kz'
        },
        {
            'chave': 'DIAS_LIMITE_PAGAMENTO',
            'valor': '3',
            'descricao': 'Dias limite para pagamento após confirmação'
        },
        {
            'chave': 'PERCENTAGEM_DISPUTA',
            'valor': '0.05',
            'descricao': 'Taxa administrativa para disputas (5%)'
        }
    ]
    
    for config_data in configs:
        config = ConfiguracaoSistema.query.filter_by(
            chave=config_data['chave']
        ).first()
        
        if not config:
            config = ConfiguracaoSistema(**config_data)
            db.session.add(config)
            print(f"  ✓ Config: {config_data['chave']} = {config_data['valor']}")
    
    db.session.commit()
    print("  ✅ Configurações criadas!\n")


def main():
    """Função principal de seed"""
    print("\n" + "="*70)
    print("🌱 AGROKONGO - SCRIPT DE SEED")
    print("="*70 + "\n")
    
    app = create_app('development')
    
    with app.app_context():
        try:
            print("✅ Verificando conexões com banco de dados...")
            db.session.execute('SELECT 1')
            print("   Banco de dados conectado!\n")
            
            # Executar seeds
            criar_provincias_municipios()
            criar_administradores()
            criar_usuarios_exemplo()
            criar_produtos()
            criar_safras_exemplo()
            criar_configuracoes_sistema()
            
            print("\n" + "="*70)
            print("🎉 SEED CONCLUÍDO COM SUCESSO!")
            print("="*70)
            print("\nDados criados:")
            print("  • 4 províncias com 14 municípios")
            print("  • 1 administrador")
            print("  • 2 usuários de exemplo (1 produtor, 1 comprador)")
            print("  • 8 produtos agrícolas")
            print("  • 3 safras de exemplo")
            print("  • 5 configurações do sistema")
            print("\nCredenciais de acesso:")
            print("  👨‍💼 Admin: admin@agrokongo.ao / Admin123!")
            print("  👨‍🌾 Produtor: joao.silva@example.ao / Produtor123!")
            print("  👤 Comprador: maria.santos@example.ao / Comprador123!")
            print("\n" + "="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERRO AO EXECUTAR SEED: {e}")
            db.session.rollback()
            sys.exit(1)


if __name__ == '__main__':
    main()
