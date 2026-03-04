import os
from dotenv import load_dotenv

# 1. Carregar variáveis do .env primeiro que tudo
load_dotenv()

# 2. Forçar explicitamente o ambiente de desenvolvimento
os.environ['FLASK_ENV'] = 'development'



from datetime import datetime, timezone
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import (
    Provincia, Municipio, Produto, Usuario, Carteira,
    Transacao, Safra, HistoricoStatus, TransactionStatus, Notificacao, LogAuditoria
)



app = create_app('dev')


def gerir_base_dados():
    with app.app_context():
        print("🚀 [START] Iniciando operações de base de dados...")

        # 1. Limpeza e Recriação (Ambiente de Dev)
        print("♻️  Limpando base de dados antiga...")
        db.drop_all()
        print("🏗️  Criando novas tabelas...")
        db.create_all()

        # 2. Dados Geográficos de Angola (lista canónica definida por lei vigente)
        print("🌍 Populando geografia angolana...")
        # Carregar lista canónica a partir de JSON (Lei 14/24)
        import json, os as _os
        data_path = _os.path.join(app.root_path, 'data', 'ao_divisoes.json')
        with open(data_path, 'r', encoding='utf-8') as f:
            geo = json.load(f)
        for prov in geo:
            p = Provincia(nome=prov['nome'])
            db.session.add(p)
            db.session.flush()
            for m in prov.get('municipios', []):
                db.session.add(Municipio(nome=m['nome'], provincia_id=p.id))

        # 3. Produtos Base
        PRODUTOS = [
            ('Mandioca', 'Raízes'),
            ('Batata Doce', 'Raízes'),
            ('Milho', 'Cereais'),
            ('Ginguba', 'Leguminosas'),
            ('Banana Pão', 'Frutas')
        ]
        for nome_p, cat in PRODUTOS:
            db.session.add(Produto(nome=nome_p, categoria=cat))
        db.session.flush()

        # 4. Utilizadores de Teste
        print("👥 Criando perfis de teste...")

        # Admin
        admin = Usuario(
            nome="Admin AgroKongo",
            telemovel="942050656",
            email="admin@agrokongo.com",
            tipo="admin",
            perfil_completo=True,
            conta_validada=True
        )
        admin.senha = "AgroAdmin2026"  # Hash automático via Model setter
        db.session.add(admin)
        db.session.flush()

        # Criar carteira para admin
        db.session.add(Carteira(
            usuario_id=admin.id,
            saldo_disponivel=Decimal('0.00'),
            saldo_bloqueado=Decimal('0.00')
        ))

        # Localização para usuários
        mun_luanda = Municipio.query.filter_by(nome='Luanda').first()

        # Produtor (Validado e com IBAN)
        produtor = Usuario(
            nome="João Fazendeiro",
            telemovel="923000000",
            email="produtor@teste.com",
            nif="501234400001",
            tipo="produtor",
            municipio_id=mun_luanda.id,
            provincia_id=mun_luanda.provincia_id,
            iban="AO06004000001234567890123",
            perfil_completo=True,
            conta_validada=True
        )
        produtor.senha = "123456"
        db.session.add(produtor)
        db.session.flush()

        # Criar carteira para produtor
        db.session.add(Carteira(
            usuario_id=produtor.id,
            saldo_disponivel=Decimal('0.00'),
            saldo_bloqueado=Decimal('0.00')
        ))

        # Comprador
        comprador = Usuario(
            nome="Manuel Cliente",
            telemovel="931000000",
            email="comprador@teste.com",
            tipo="comprador",
            municipio_id=mun_luanda.id,
            provincia_id=mun_luanda.provincia_id,
            perfil_completo=True,
            conta_validada=True
        )
        comprador.senha = "123456"
        db.session.add(comprador)
        db.session.flush()

        # Criar carteira para comprador
        db.session.add(Carteira(
            usuario_id=comprador.id,
            saldo_disponivel=Decimal('0.00'),
            saldo_bloqueado=Decimal('0.00')
        ))

        # 5. Stock e Transações
        print("📦 Gerando stock e transações iniciais...")
        mandioca = Produto.query.filter_by(nome='Mandioca').first()

        safra_teste = Safra(
            produtor_id=produtor.id,
            produto_id=mandioca.id,
            quantidade_disponivel=Decimal('500.0'),
            preco_por_unidade=Decimal('250.0'),
            status='disponivel'
        )
        db.session.add(safra_teste)
        db.session.flush()

        # Simulação de Venda: Cálculo de Comissão (5%)
        qtd = Decimal('5.0')
        valor_total = qtd * safra_teste.preco_por_unidade
        taxa = (valor_total * Decimal('0.05')).quantize(Decimal('0.01'))
        liquido = valor_total - taxa

        venda_pendente = Transacao(
            safra_id=safra_teste.id,
            comprador_id=comprador.id,
            vendedor_id=produtor.id,
            quantidade_comprada=qtd,
            valor_total_pago=valor_total,
            comissao_plataforma=taxa,
            valor_liquido_vendedor=liquido,
            fatura_ref="AK-2026-PEND",
            status=TransactionStatus.ANALISE,
            comprovativo_path="comprovativos/comprovativo_teste.webp",
            data_criacao=datetime.now(timezone.utc)
        )
        db.session.add(venda_pendente)
        db.session.flush()

        # 6. Histórico e Notificações
        db.session.add(HistoricoStatus(
            transacao_id=venda_pendente.id,
            status_anterior=TransactionStatus.PENDENTE,
            status_novo=TransactionStatus.ANALISE,
            observacoes="Sistema: Talão submetido pelo comprador."
        ))

        db.session.add(Notificacao(
            usuario_id=admin.id,
            mensagem=f"🔔 Novo Talão: Manuel Cliente submeteu prova de pagamento (Ref: {venda_pendente.fatura_ref})",
            link=f"/admin/detalhe-transacao/{venda_pendente.id}"
        ))

        db.session.add(LogAuditoria(
            usuario_id=comprador.id,
            acao="SUBMISSÃO_PAGAMENTO",
            detalhes=f"Comprador enviou comprovativo para a transação {venda_pendente.fatura_ref}"
        ))

        db.session.commit()
        print("\n✨ Base de Dados populada com sucesso!")
        print("-" * 50)
        print(f"🌍 Geografia: 18 Províncias | 142 Municípios")
        print(f"🌾 Produtos: 5 categorias")
        print(f"👥 Usuários: 3 (Admin, Produtor, Comprador)")
        print(f"💰 Carteiras: 3 criadas")
        print("-" * 50)
        print(f"🔑 ADMIN:    942050656 / AgroAdmin2026")
        print(f"🔑 PRODUTOR: 923000000 / 123456")
        print(f"🔑 COMPRADOR: 931000000 / 123456")
        print("-" * 50)


if __name__ == "__main__":
    gerir_base_dados()