# Validação rápida da correção
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("VALIDANDO CORREÇÃO - AGROKONGO")
print("=" * 80)

try:
    print("\n📦 Importando create_app...")
    from app import create_app
    
    print("✅ Criando app com configuração 'dev'...")
    app = create_app('dev')
    
    print("✅ App criado com sucesso!")
    
    print("\n📋 Verificando blueprints registrados...")
    blueprints = list(app.blueprints.keys())
    print(f"   Total de blueprints: {len(blueprints)}")
    print(f"   Blueprints: {', '.join(blueprints[:5])}...")
    
    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO BEM-SUCEDIDA!")
    print("=" * 80)
    print("\nOs testes agora podem ser executados:")
    print("   pytest tests/integration/ -v")
    print("   pytest --cov=app --cov-report=html")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
