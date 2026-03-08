"""
Script de validação rápida dos testes
"""
import sys
from pathlib import Path

# Adicionar root ao path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

print("="*70)
print("🧪 VALIDANDO IMPORTAÇÃO DOS TESTES")
print("="*70)

try:
    print("\n1. Testando import do conftest...")
    from tests_framework import conftest
    print("   ✅ conftest importado com sucesso!")
    
    print("\n2. Testando import do test_auth_security...")
    from tests_framework import test_auth_security
    print("   ✅ test_auth_security importado com sucesso!")
    
    print("\n3. Testando import do test_financial_transactions...")
    from tests_framework import test_financial_transactions
    print("   ✅ test_financial_transactions importado com sucesso!")
    
    print("\n4. Verificando modelos...")
    from app.models import Usuario, Provincia, Municipio, Transacao, Safra
    print("   ✅ Modelos importados com sucesso!")
    
    print("\n" + "="*70)
    print("🎉 TODAS AS IMPORTAÇÕES FUNCIONAM CORRETAMENTE!")
    print("="*70)
    print("\nAgora você pode rodar os testes com:")
    print("  python -m pytest tests_framework/test_auth_security.py -v")
    print("  python -m pytest tests_framework/test_financial_transactions.py -v")
    print("  make test-framework  (se estiver usando Makefile)")
    print()
    
except Exception as e:
    print(f"\n❌ ERRO NA IMPORTAÇÃO: {e}")
    print(f"\nDetalhes:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
