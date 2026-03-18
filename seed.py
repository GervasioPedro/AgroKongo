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
    Provincia, Municipio, Produto, Usuario,
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

        # 2. Dados Geográficos Reais (Angola)
        print("🌍 Populando geografia angolana...")
        DADOS_GEOGRAFICOS = {
            'Zaire': ['Mbanza Kongo', 'Soyo', 'Nzeto', 'Tomboco', 'Cuimba', 'Nóqui'],
            'Uíge': ['Negage', 'Puri', 'Songo', 'Uíge', 'Maquela do Zombo'],
            'Luanda': ['Belas', 'Cacuaco', 'Cazenga', 'Talatona', 'Viana'],
            'Bengo': ['Caxito', 'Ambriz', 'Dande']
        }

        for nome_prov, municipios in DADOS_GEOGRAFICOS.items():
            prov = Provincia(nome=nome_prov)
            db.session.add(prov)
            db.session.flush()  # Obtém ID da província
            for nome_mun in municipios:
                db.session.add(Municipio(nome=nome_mun, provincia_id=prov.id))

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
            telemovel="900000000",
            email="admin@agrokongo.com",
            tipo="admin",
            perfil_completo=True,
            conta_validada=True
        )
        admin.senha = "AgroAdmin2026"  # Hash automático via Model setter
        db.session.add(admin)

        # Localização para usuários
        mun_zaire = Municipio.query.filter_by(nome='Mbanza Kongo').first()

        # Produtor (Validado e com IBAN)
        produtor = Usuario(
            nome="João Fazendeiro",
            telemovel="923000000",
            email="produtor@teste.com",
            nif="501234400001",
            tipo="produtor",
            municipio_id=mun_zaire.id,
            provincia_id=mun_zaire.provincia_id,
            iban="AO06004000001234567890123",
            perfil_completo=True,
            conta_validada=True
        )
        produtor.senha = "123456"
        db.session.add(produtor)

        # Comprador
        comprador = Usuario(
            nome="Manuel Cliente",
            telemovel="931000000",
            email="comprador@teste.com",
            tipo="comprador",
            municipio_id=mun_zaire.id,
            provincia_id=mun_zaire.provincia_id,
            perfil_completo=True,
            conta_validada=True
        )
        comprador.senha = "123456"
        db.session.add(comprador)
        db.session.flush()

        # 5. Stock e Transações
        print("📦 Gerando stock e transações iniciais...")
        mandioca = Produto.query.filter_by(nome='Mandioca').first()

        safra_teste = Safra(
            produtor_id=produtor.id,
            produto_id=mandioca.id,
            quantidade_disponivel=Decimal('500.0'),
            preco_por_unidade=Decimal('250.0'),
            status='disponivel',
            imagem='safras/default_safra.webp'
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
            status=TransactionStatus.ANALISE, # <-- CORREÇÃO: Usar o valor diretamente
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
            observacao="Sistema: Talão submetido pelo comprador."
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
        print("-" * 30)
        print(f"🔑 ADMIN:    admin@agrokongo.com / AgroAdmin2026")
        print(f"🔑 PRODUTOR: produtor@teste.com / 123456")
        print(f"🔑 CLIENTE:  comprador@teste.com / 123456")
        print("-" * 30)


if __name__ == "__main__":
    gerir_base_dados()