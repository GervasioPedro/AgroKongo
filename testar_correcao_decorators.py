# Script para testar correções dos decorators
import sys

print("=" * 80)
print("TESTANDO CORREÇÕES - DECORATORS")
print("=" * 80)

try:
    # Testar import
    print("\n1. Testando imports...")
    from app.utils.decorators import admin_required, produtor_required
    from app.models import LogAuditoria
    print("   ✅ Imports OK")
    
    # Testar estrutura do LogAuditoria
    print("\n2. Verificando campos do LogAuditoria...")
    from app.extensions import db
    print(f"   Campos: {[c.name for c in LogAuditoria.__table__.columns]}")
    
    if 'ip_address' in [c.name for c in LogAuditoria.__table__.columns]:
        print("   ✅ Campo 'ip_address' existe")
    else:
        print("   ❌ Campo 'ip_address' NÃO existe")
        
    if 'data_acao' in [c.name for c in LogAuditoria.__table__.columns]:
        print("   ✅ Campo 'data_acao' existe")
    else:
        print("   ❌ Campo 'data_acao' NÃO existe")
    
    # Verificar handlers.py
    print("\n3. Verificando handlers.py...")
    with open('app/routes/handlers.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'ip_address=request.remote_addr' in content:
            print("   ✅ handlers.py usando 'ip_address' corretamente")
        else:
            print("   ❌ handlers.py NÃO está usando 'ip_address'")
            
        if 'data_acao=aware_utcnow()' in content:
            print("   ✅ handlers.py usando 'data_acao' corretamente")
        else:
            print("   ❌ handlers.py NÃO está usando 'data_acao'")
    
    # Verificar decorators.py
    print("\n4. Verificando decorators.py...")
    with open('app/utils/decorators.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'ip_address=request.remote_addr' in content:
            print("   ✅ decorators.py usando 'ip_address' corretamente")
        else:
            print("   ❌ decorators.py NÃO está usando 'ip_address'")
        
        if 'ACESSO_NEGADO_ADMIN' in content:
            print("   ✅ decorators.py com log de auditoria correto")
        else:
            print("   ❌ decorators.py SEM log de auditoria")
    
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO CONCLUÍDA!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
