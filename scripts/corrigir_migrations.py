#!/usr/bin/env python3
"""
Script para corrigir migrations órfãs do Alembic
Remove referências a migrations que não existem mais
"""
import os
import sys

# Adiciona o projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['FLASK_ENV'] = 'dev'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['DATABASE_URL'] = 'postgresql://agrokongo_user:agrokongo_pass@localhost:5433/agrokongo_dev'

from app import create_app
from app.extensions import db

def main():
    print("=" * 70)
    print("🔧 CORRIGIR MIGRATIONS ÓRFÃS")
    print("=" * 70)
    
    app = create_app('dev')
    
    with app.app_context():
        # Verificar tabela alembic_version
        from sqlalchemy import inspect, text
        
        inspector = inspect(db.engine)
        
        if 'alembic_version' not in inspector.get_table_names():
            print("\n✅ Tabela alembic_version não existe. Banco limpo!")
            print("💡 Execute: flask db upgrade heads")
            return True
        
        # Ler versão atual
        result = db.session.execute(text("SELECT version_num FROM alembic_version")).fetchall()
        
        if not result:
            print("\n✅ Tabela alembic_version vazia. Banco limpo!")
            print("💡 Execute: flask db upgrade heads")
            return True
        
        versions = [row[0] for row in result]
        print(f"\n📊 Versões encontradas: {versions}")
        
        # Verificar se há referência órfã
        orphan_version = '28abd6f2be3a'
        
        if orphan_version in versions:
            print(f"\n⚠️  Encontrada referência órfã: {orphan_version}")
            print("🗑️  Removendo...")
            
            db.session.execute(text(f"DELETE FROM alembic_version WHERE version_num = '{orphan_version}'"))
            db.session.commit()
            
            print("✅ Referência removida com sucesso!")
            
            # Agora tentar aplicar migrations
            print("\n🚀 Aplicando migrations restantes...")
            print("💡 Execute: flask db upgrade heads")
            return True
        else:
            print(f"\n✅ Sem referência órfã {orphan_version}")
            
            # Mostrar última versão
            print(f"\n📊 Última versão: {versions[-1] if versions else 'Nenhuma'}")
            print("\n💡 Se quiser recriar migrations do zero:")
            print("   1. docker-compose down -v")
            print("   2. docker-compose up -d db")
            print("   3. flask db stamp <base>")
            print("   4. flask db upgrade heads")
            return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
