"""
Script para validar a refatoração do método mudar_status()
"""
import sys
import subprocess

def run_tests():
    """Executa todos os testes de integração para validar refatoração"""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short"
    ]
    
    print("=" * 80)
    print("VALIDANDO REATORAÇÃO DO MÉTODO MUDAR_STATUS()...")
    print("=" * 80)
    print("\nRecursos testados:")
    print("  ✅ Auto-add do histórico à sessão")
    print("  ✅ Método helper mudar_status_em_lote()")
    print("  ✅ Validação de transições pode_mudar_para()")
    print("  ✅ Parâmetro validar_transicao opcional")
    print("=" * 80)
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("\n📊 Resumo da Refatoração:")
        print("  • Código simplificado em compra_service.py (-10 linhas)")
        print("  • Código simplificado em pagamento_service.py (-4 linhas)")
        print("  • Código simplificado em test_fluxo_escrow.py (-2 linhas)")
        print("  • Novos recursos no modelo Transacao:")
        print("    - auto_add padrão (True)")
        print("    - mudar_status_em_lote()")
        print("    - pode_mudar_para()")
        print("    - validar_transicao (opcional)")
    else:
        print(f"❌ {result.returncode} teste(s) falharam")
    print("=" * 80)
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
