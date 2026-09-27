"""Popula a base de dados com dados de demonstração do AgroKongo.

Substituto Django do `seed.py` do Flask. Uso:

    python manage.py seed          # idempotente (get_or_create)
    python manage.py seed --reset  # apaga tudo e recria (apenas dev!)
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction

from apps.accounts.models import Usuario
from apps.catalogo.models import Produto, Safra
from apps.geo.models import Municipio, Provincia

DADOS_GEOGRAFICOS = {
    # nome: (codigo INE, municipios)
    "Zaire": (1, ["Mbanza Kongo", "Soyo", "Nzeto", "Tomboco", "Cuimba", "Nóqui"]),
    "Uíge": (8, ["Negage", "Puri", "Songo", "Uíge", "Maquela do Zombo"]),
    "Luanda": (30, ["Belas", "Cacuaco", "Cazenga", "Talatona", "Viana"]),
    "Bengo": (29, ["Caxito", "Ambriz", "Dande"]),
}

PRODUTOS = [
    ("Mandioca", "Raízes"),
    ("Batata Doce", "Raízes"),
    ("Milho", "Cereais"),
    ("Ginguba", "Leguminosas"),
    ("Banana Pão", "Frutas"),
]


class Command(BaseCommand):
    help = "Popula a base de dados com dados geográficos, produtos e utilizadores demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Apaga os dados existentes antes de semear (apenas em desenvolvimento).",
        )

    @db_transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("♻️  A limpar tabelas..."))
            Safra.objects.all().delete()
            Usuario.objects.all().delete()
            Produto.objects.all().delete()
            Municipio.objects.all().delete()
            Provincia.objects.all().delete()

        # 1. Geografia (id = codigo INE — PK explícita, sem autoincrement)
        for nome_prov, (codigo, municipios) in DADOS_GEOGRAFICOS.items():
            prov, _ = Provincia.objects.get_or_create(
                id=codigo, defaults={"nome": nome_prov, "codigo": codigo}
            )
            for nome_mun in municipios:
                Municipio.objects.get_or_create(nome=nome_mun, provincia=prov)
        self.stdout.write(f"🌍 Geografia: {Provincia.objects.count()} províncias, "
                          f"{Municipio.objects.count()} municípios")

        # 2. Produtos
        for nome_p, cat in PRODUTOS:
            Produto.objects.get_or_create(nome=nome_p, defaults={"categoria": cat})
        self.stdout.write(f"🥔 Produtos: {Produto.objects.count()}")

        # 3. Utilizadores demo
        admin, created = Usuario.objects.get_or_create(
            telemovel="+244920000000",
            defaults={
                "nome": "Admin AgroKongo", "email": "admin@agrokongo.com",
                "tipo": Usuario.Tipos.ADMIN, "perfil_completo": True,
                "conta_validada": True, "is_staff": True, "is_superuser": True,
            },
        )
        if created:
            admin.set_password("AgroAdmin2026")
            admin.save()

        mun = Municipio.objects.filter(nome="Mbanza Kongo").first()

        produtor, created = Usuario.objects.get_or_create(
            telemovel="+244923000000",
            defaults={
                "nome": "João Fazendeiro", "email": "produtor@teste.com",
                "nif": "501234400001", "tipo": Usuario.Tipos.PRODUTOR,
                "provincia": mun.provincia if mun else None, "municipio": mun,
                "iban": "AO06004000001234567890123",
                "perfil_completo": True, "conta_validada": True,
                # documento_pdf é obrigatório p/ kyc_aprovado (permite reservar)
                "documento_pdf": "kyc_produtor_seed.pdf",
            },
        )
        if created:
            produtor.set_password("123456")
            produtor.save()

        comprador, created = Usuario.objects.get_or_create(
            telemovel="+244931000000",
            defaults={
                "nome": "Manuel Cliente", "email": "comprador@teste.com",
                "tipo": Usuario.Tipos.COMPRADOR,
                "provincia": mun.provincia if mun else None, "municipio": mun,
                "perfil_completo": True, "conta_validada": True,
                "documento_pdf": "kyc_comprador_seed.pdf",
            },
        )
        if created:
            comprador.set_password("123456")
            comprador.save()

        # 4. Safras de exemplo
        mandioca = Produto.objects.get(nome="Mandioca")
        milho = Produto.objects.get(nome="Milho")
        if not Safra.objects.exists():
            Safra.objects.create(
                produtor=produtor, produto=mandioca,
                quantidade_disponivel=Decimal("500.0"),
                preco_por_unidade=Decimal("250.0"),
                status=Safra.Statuses.DISPONIVEL,
            )
            Safra.objects.create(
                produtor=produtor, produto=milho,
                quantidade_disponivel=Decimal("1200.0"),
                preco_por_unidade=Decimal("180.0"),
                status="disponivel",
            )
        self.stdout.write(f"📦 Safras: {Safra.objects.count()}")

        self.stdout.write(self.style.SUCCESS("\n✨ Base de dados populada com sucesso!"))
        self.stdout.write("-" * 30)
        self.stdout.write("🔑 ADMIN:     +244920000000 / AgroAdmin2026")
        self.stdout.write("🔑 PRODUTOR:  +244923000000 / 123456")
        self.stdout.write("🔑 CLIENTE:   +244931000000 / 123456")
