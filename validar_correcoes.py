"""
Validação final das correções do histórico de status
"""
import sys
import subprocess

def run_all_tests():
    """Executa todos os testes de integração"""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ]
    
    print("=" * 80)
    print("EXECUTANDO TODOS OS TESTES DE INTEGRAÇÃO...")
    print("=" * 80)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print(f"❌ {result.returncode} teste(s) falharam")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
