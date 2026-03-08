#!/usr/bin/env python3
"""
Script para testar importação de todos os modelos
"""
import sys
import os

# Adiciona o projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ['FLASK_ENV'] = 'dev'
os.environ['SECRET_KEY'] = 'test-secret-key'

print("=" * 70)
print("🧪 TESTE DE IMPORTAÇÃO DOS MODELOS")
print("=" * 70)

try:
    print("\n1️⃣ Testando app.models.base...")
    from app.models.base import aware_utcnow, TransactionStatus, StatusConta
    print("   ✅ base OK")
    
    print("\n2️⃣ Testando app.models.usuario...")
    from app.models.usuario import Usuario, Provincia, Municipio
    print("   ✅ usuario OK")
    
    print("\n3️⃣ Testando app.models.produto...")
    from app.models.produto import Produto, Safra
    print("   ✅ produto OK")
    
    print("\n4️⃣ Testando app.models.transacao...")
    from app.models.transacao import Transacao, HistoricoStatus
    print("   ✅ transacao OK")
    
    print("\n5️⃣ Testando app.models.avaliacao...")
    from app.models.avaliacao import Avaliacao
    print("   ✅ avaliacao OK")
    
    print("\n6️⃣ Testando app.models.financeiro...")
    from app.models.financeiro import Carteira, MovimentacaoFinanceira
    print("   ✅ financeiro OK")
    
    print("\n7️⃣ Testando app.models.notificacao...")
    from app.models.notificacao import Notificacao, AlertaPreferencia
    print("   ✅ notificacao OK")
    
    print("\n8️⃣ Testando app.models.disputa...")
    from app.models.disputa import Disputa
    print("   ✅ disputa OK")
    
    print("\n9️⃣ Testando app.models.auditoria...")
    from app.models.auditoria import LogAuditoria, ConfiguracaoSistema
    print("   ✅ auditoria OK")
    
    print("\n🔟 Testando app.models.lgpd...")
    from app.models.lgpd import ConsentimentoLGPD, RegistroAnonimizacao
    print("   ✅ lgpd OK")
    
    print("\n" + "=" * 70)
    print("✅ TODOS OS MODELOS IMPORTARAM CORRETAMENTE!")
    print("=" * 70)
    
    # Agora testar import consolidado
    print("\n📦 Testando import consolidado (app.models)...")
    from app.models import (
        Usuario, Produto, Safra, Transacao, HistoricoStatus,
        Carteira, MovimentacaoFinanceira, Notificacao, Disputa,
        LogAuditoria, Avaliacao
    )
    print("   ✅ Import consolidado OK!")
    
    print("\n" + "=" * 70)
    print("🎉 SUCESSO! Todos os modelos estão funcionando!")
    print("=" * 70)
    
except ImportError as e:
    print(f"\n❌ ERRO DE IMPORTAÇÃO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERRO INESPERADO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
