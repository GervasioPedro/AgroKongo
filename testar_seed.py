"""
Script para testar a correção do seed.py
"""
import sys
import subprocess

def test_seed():
    """Executa o seed.py para validar a correção"""
    cmd = [
        sys.executable,
        "seed.py"
    ]
    
    print("=" * 80)
    print("TESTANDO CORREÇÃO DO SEED.PY...")
    print("=" * 80)
    print("\nCorreções aplicadas:")
    print("  ✅ Adicionado import: status_to_value")
    print("  ✅ Corrigido: status=TransactionStatus.X → status=status_to_value(TransactionStatus.X)")
    print("  ✅ Corrigido: HistoricoStatus usando status_to_value()")
    print("=" * 80)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ SEED EXECUTADO COM SUCESSO!")
    else:
        print(f"❌ ERRO AO EXECUTAR SEED (código {result.returncode})")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = test_seed()
    sys.exit(exit_code)
