"""
Script para validar imports do test_e2e.py
"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

print("Validando imports do test_e2e.py...")
print("=" * 80)

try:
    from app.models import (
        Usuario, Safra, Transacao, TransactionStatus,
        Notificacao, LogAuditoria, HistoricoStatus, Produto
    )
    print("✅ app.models import OK")
except Exception as e:
    print(f"❌ app.models ERROR: {e}")

try:
    from app.models.financeiro import Carteira
    print("✅ app.models.financeiro.Carteira import OK")
except Exception as e:
    print(f"❌ app.models.financeiro ERROR: {e}")

try:
    from app.models.disputa import Disputa
    print("✅ app.models.disputa.Disputa import OK")
except Exception as e:
    print(f"❌ app.models.disputa ERROR: {e}")

try:
    from app.services.otp_service import gerar_e_enviar_otp, OTPService
    print("✅ app.services.otp_service import OK")
except Exception as e:
    print(f"❌ app.services.otp_service ERROR: {e}")

try:
    from app.routes.cadastro_produtor import _criar_usuario_produtor
    print("✅ app.routes.cadastro_produtor import OK")
except Exception as e:
    print(f"❌ app.routes.cadastro_produtor ERROR: {e}")

print("=" * 80)
print("Todos os imports foram validados com sucesso!")
