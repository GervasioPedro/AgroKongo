"""
Script para testar as 3 correções principais:
1. Histórico de status sendo persistido
2. Stock sendo reposto na recusa
3. Notificação com texto correto
"""
import sys
import subprocess

def run_tests():
    """Executa os testes que estavam falhando"""
    tests = [
        "tests/integration/test_fluxo_escrow.py::TestFluxoEscrowCompleto::test_fluxo_completo_escrow",
        "tests/integration/test_fluxo_escrow.py::TestFluxoEscrowCompleto::test_recusar_reserva_repoe_stock",
        "tests/integration/test_fluxos_adicionais.py::TestRecusarReserva::test_recusar_reserva_repoe_stock"
    ]
    
    cmd = [
        sys.executable,
        "-m",
        "pytest"
    ] + tests + [
        "-xvs",  # Verbose, stop on first failure
        "--tb=short"  # Shorter traceback output
    ]
    
    print("=" * 80)
    print("EXECUTANDO TESTES DAS 3 CORREÇÕES...")
    print("=" * 80)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES AINDA ESTÃO FALHANDO")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
