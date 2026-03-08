"""
Validação completa de todos os imports do projeto
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

print("="*70)
print("🔍 VALIDANDO IMPORTS DO PROJETO AGROKONGO")
print("="*70)

erros = []

# 1. Validar imports básicos
print("\n1️⃣  Imports básicos...")
try:
    from app.extensions import db, cache
    print("   ✅ app.extensions")
except Exception as e:
    erros.append(f"app.extensions: {e}")
    print(f"   ❌ app.extensions: {e}")

try:
    from app.models.base import aware_utcnow, TransactionStatus, StatusConta
    print("   ✅ app.models.base")
except Exception as e:
    erros.append(f"app.models.base: {e}")
    print(f"   ❌ app.models.base: {e}")

# 2. Validar modelos individualmente
print("\n2️⃣  Modelos individuais...")

modelos_para_testar = [
    ("Usuario, Provincia, Municipio", "app.models.usuario"),
    ("Transacao, HistoricoStatus", "app.models.transacao"),
    ("Produto, Safra", "app.models.produto"),
    ("Carteira, MovimentacaoFinanceira", "app.models.financeiro"),
    ("Notificacao, AlertaPreferencia", "app.models.notificacao"),
    ("Disputa", "app.models.disputa"),
    ("LogAuditoria, ConfiguracaoSistema", "app.models.auditoria"),
    ("Avaliacao", "app.models.avaliacao"),
    ("ConsentimentoLGPD, RegistroAnonimizacao", "app.models.lgpd"),
]

for nomes, modulo in modelos_para_testar:
    try:
        exec(f"from {modulo} import {nomes}")
        print(f"   ✅ {modulo}")
    except Exception as e:
        erros.append(f"{modulo}: {e}")
        print(f"   ❌ {modulo}: {str(e)[:60]}")

# 3. Validar import consolidado
print("\n3️⃣  Import consolidado (app.models)...")
try:
    from app.models import (
        Usuario, Provincia, Municipio,
        Transacao, HistoricoStatus,
        Produto, Safra,
        Carteira, MovimentacaoFinanceira,
        Notificacao, AlertaPreferencia,
        Disputa,
        LogAuditoria, ConfiguracaoSistema,
        Avaliacao,
        ConsentimentoLGPD, RegistroAnonimizacao
    )
    print("   ✅ Todos os modelos importados com sucesso!")
except Exception as e:
    erros.append(f"app.models consolidado: {e}")
    print(f"   ❌ app.models consolidado: {str(e)[:60]}")

# 4. Validar blueprints
print("\n4️⃣  Blueprints...")
try:
    from app.routes.health import health_bp
    print("   ✅ app.routes.health")
except Exception as e:
    erros.append(f"app.routes.health: {e}")
    print(f"   ❌ app.routes.health: {str(e)[:60]}")

try:
    from app.routes.api_v1 import api_v1_bp
    print("   ✅ app.routes.api_v1")
except Exception as e:
    erros.append(f"app.routes.api_v1: {e}")
    print(f"   ❌ app.routes.api_v1: {str(e)[:60]}")

# 5. Validar aplicação Flask
print("\n5️⃣  Aplicação Flask...")
try:
    from app import create_app
    print("   ✅ app.create_app")
except Exception as e:
    erros.append(f"app.create_app: {e}")
    print(f"   ❌ app.create_app: {str(e)[:60]}")

# 6. Testes
print("\n6️⃣  Framework de testes...")
try:
    from tests_framework.conftest import app as test_app_fixture
    print("   ✅ tests_framework.conftest")
except Exception as e:
    erros.append(f"tests_framework.conftest: {e}")
    print(f"   ❌ tests_framework.conftest: {str(e)[:60]}")

try:
    import tests_framework.test_auth_security
    print("   ✅ tests_framework.test_auth_security")
except Exception as e:
    erros.append(f"tests_framework.test_auth_security: {e}")
    print(f"   ❌ tests_framework.test_auth_security: {str(e)[:60]}")

try:
    import tests_framework.test_financial_transactions
    print("   ✅ tests_framework.test_financial_transactions")
except Exception as e:
    erros.append(f"tests_framework.test_financial_transactions: {e}")
    print(f"   ❌ tests_framework.test_financial_transactions: {str(e)[:60]}")

# Resumo final
print("\n" + "="*70)
if not erros:
    print("🎉 TODOS OS IMPORTS FUNCIONAM CORRETAMENTE!")
    print("="*70)
    print("\n✅ Projeto pronto para:")
    print("   • Rodar testes com pytest")
    print("   • Iniciar servidor de desenvolvimento")
    print("   • Executar migrations")
    print("   • Popular banco com seed data")
    print()
else:
    print(f"❌ {len(erros)} ERRO(S) ENCONTRADO(S):")
    print("="*70)
    for i, erro in enumerate(erros, 1):
        print(f"\n{i}. {erro}")
    print()
    sys.exit(1)
