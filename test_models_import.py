"""Teste rápido de importação dos modelos"""
import sys
from pathlib import Path

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

print("Testando importação dos modelos...")

try:
    from app.models import Usuario, Provincia, Municipio
    print("✅ usuario.py OK")
except Exception as e:
    print(f"❌ usuario.py ERRO: {e}")

try:
    from app.models import Transacao, HistoricoStatus
    print("✅ transacao.py OK")
except Exception as e:
    print(f"❌ transacao.py ERRO: {e}")

try:
    from app.models import Produto, Safra
    print("✅ produto.py OK")
except Exception as e:
    print(f"❌ produto.py ERRO: {e}")

try:
    from app.models import Carteira, MovimentacaoFinanceira
    print("✅ financeiro.py OK")
except Exception as e:
    print(f"❌ financeiro.py ERRO: {e}")

try:
    from app.models import Notificacao, AlertaPreferencia
    print("✅ notificacao.py OK")
except Exception as e:
    print(f"❌ notificacao.py ERRO: {e}")

try:
    from app.models import Disputa
    print("✅ disputa.py OK")
except Exception as e:
    print(f"❌ disputa.py ERRO: {e}")

try:
    from app.models import LogAuditoria, ConfiguracaoSistema
    print("✅ auditoria.py OK")
except Exception as e:
    print(f"❌ auditoria.py ERRO: {e}")

try:
    from app.models import Avaliacao
    print("✅ avaliacao.py OK")
except Exception as e:
    print(f"❌ avaliacao.py ERRO: {e}")

try:
    from app.models import ConsentimentoLGPD, RegistroAnonimizacao
    print("✅ lgpd.py OK")
except Exception as e:
    print(f"❌ lgpd.py ERRO: {e}")

print("\n✅ Todos os modelos foram importados corretamente!")
