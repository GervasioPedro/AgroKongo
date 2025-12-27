import os
import sys

# Garante que o Python encontre a pasta 'app' mesmo estando fora dela
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from extensions import db
from core.models import Provincia, Municipio, Produto  # Import do Produto adicionado

DADOS_GEOGRAFICOS = {
    'Bengo': ['Ambriz', 'Bula Atumba', 'Dande', 'Dembos', 'Nambuangongo', 'Pango Aluquém'],
    'Benguela': ['Baía Farta', 'Balombo', 'Benguela', 'Bocoio', 'Caimbambo', 'Catumbela', 'Chongorói', 'Cubal', 'Ganda',
                 'Lobito'],
    'Bié': ['Andulo', 'Camacupa', 'Catabola', 'Chinguar', 'Chitembo', 'Cuemba', 'Cunhinga', 'Cuíto', 'Nharea'],
    'Cabinda': ['Belize', 'Buco-Zau', 'Cabinda', 'Cacongo'],
    'Cuando Cubango': ['Calai', 'Cuangar', 'Cuchi', 'Cuito Cuanavale', 'Dirico', 'Mavinga', 'Menongue', 'Nancova',
                       'Rivungo'],
    'Cuanza Norte': ['Ambaca', 'Banga', 'Bolongongo', 'Cambambe', 'Cazengo', 'Golungo Alto', 'Gonguembo', 'Lucala',
                     'Quiculungo', 'Samba Cajú'],
    'Cuanza Sul': ['Amboim', 'Cassongue', 'Cela', 'Conda', 'Ebo', 'Libolo', 'Mussende', 'Quibala', 'Quilenda',
                   'Porto Amboim', 'Seles', 'Sumbe'],
    'Cunene': ['Cahama', 'Cuanhama', 'Curoca', 'Cuvelai', 'Namacunde', 'Ombadja'],
    'Huambo': ['Bailundo', 'Caála', 'Cachiungo', 'Chicala-Choloanga', 'Chinjenje', 'Ecunha', 'Huambo', 'Londuimbali',
               'Longonjo', 'Mungo', 'Ucuma'],
    'Huíla': ['Caconda', 'Cacula', 'Caluquembe', 'Chiange', 'Chibia', 'Chicomba', 'Chipindo', 'Cuvango', 'Humpata',
              'Jamba', 'Lubango', 'Matala', 'Quilengues', 'Quipungo'],
    'Luanda': ['Belas', 'Cacuaco', 'Cazenga', 'Icolo e Bengo', 'Luanda', 'Quiçama', 'Kilamba Kiaxi', 'Talatona',
               'Viana'],
    'Lunda Norte': ['Cambulo', 'Capenda-Camulemba', 'Caungula', 'Chitato', 'Cuango', 'Cuilo', 'Lóvua', 'Lubalo',
                    'Lucapa', 'Xá-Muteba'],
    'Lunda Sul': ['Cacolo', 'Dala', 'Muconda', 'Saurimo'],
    'Malanje': ['Cacuso', 'Calandula', 'Cambundi-Catembo', 'Cangandala', 'Caombo', 'Cuaba Nzogo', 'Cunda-dia-Baze',
                'Luquembo', 'Malanje', 'Marimba', 'Massango', 'Mucari', 'Quela', 'Quirima'],
    'Moxico': ['Alto Zambeze', 'Bundas', 'Camanongue', 'Cameia', 'Léua', 'Luau', 'Luacano', 'Luchazes', 'Moxico'],
    'Namibe': ['Bibala', 'Camacuio', 'Moçâmedes', 'Tômbua', 'Virei'],
    'Uíge': ['Alto Cauale', 'Ambuíla', 'Bembe', 'Buengas', 'Bungo', 'Damba', 'Milunga', 'Mucaba', 'Negage', 'Puri',
             'Quimbele', 'Quitexe', 'Sanza Pombo', 'Songo', 'Uíge', 'Zombo'],
    'Zaire': ['Cuimba', 'Mbanza Kongo', 'Noqui', 'Nzeto', 'Soyo', 'Tomboco']
}

PRODUTOS_INICIAIS = [
    {'nome': 'Mandioca', 'categoria': 'Raízes'},
    {'nome': 'Batata Doce', 'categoria': 'Raízes'},
    {'nome': 'Milho Branco', 'categoria': 'Cereais'},
    {'nome': 'Feijão Catarino', 'categoria': 'Leguminosas'},
    {'nome': 'Ginguba (Amendoim)', 'categoria': 'Oleaginosas'},
    {'nome': 'Banana Pão', 'categoria': 'Frutas'},
    {'nome': 'Manga', 'categoria': 'Frutas'}
]


def seed_database():
    app = create_app()
    with app.app_context():
        print("--- Iniciando o Seeding Geral ---")

        # 1. Seeding de Localizações
        for nome_provincia, municipios in DADOS_GEOGRAFICOS.items():
            provincia = Provincia.query.filter_by(nome=nome_provincia).first()
            if not provincia:
                provincia = Provincia(nome=nome_provincia)
                db.session.add(provincia)
                db.session.flush()

            for nome_municipio in municipios:
                if not Municipio.query.filter_by(nome=nome_municipio, provincia_id=provincia.id).first():
                    db.session.add(Municipio(nome=nome_municipio, provincia_id=provincia.id))

        print("✅ Localizações processadas.")

        # 2. Seeding de Produtos
        for p in PRODUTOS_INICIAIS:
            if not Produto.query.filter_by(nome=p['nome']).first():
                db.session.add(Produto(nome=p['nome'], categoria=p['categoria']))

        print("✅ Produtos processados.")

        try:
            db.session.commit()
            print("\n🎉 Seeding concluído com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar dados: {e}")


if __name__ == "__main__":
    seed_database()