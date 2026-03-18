#!/usr/bin/env python
"""Script para executar testes e guardar resultados."""
import subprocess
import sys

# Lista de testes que falharam anteriormente
testes_para_correr = [
    "tests/integration/test_api.py::TestApiSafras::test_detalhar_safra_nao_existente",
    "tests/integration/test_correcoes.py::TestRecusarReservaFix::test_recusar_reserva_repoe_stock",
    "tests/integration/test_fluxo_escrow.py::TestFluxoEscrowCompleto::test_fluxo_completo_escrow",
    "tests/integration/test_fluxo_escrow.py::TestFluxoEscrowCompleto::test_recusar_reserva_repoe_stock",
    "tests/integration/test_fluxos_adicionais.py::TestRecusarReserva::test_recusar_reserva_repoe_stock",
    "tests/integration/test_fluxos_adicionais.py::TestRecusarReserva::test_recusar_reserva_apenas_pendente",
    "tests/integration/test_fluxos_adicionais.py::TestValidacoesSegurancaCompra::test_auto_compra_bloqueada",
    "tests/integration/test_fluxos_adicionais.py::TestValidacoesSegurancaCompra::test_compra_quantidade_indisponivel",
    "tests/integration/test_fluxos_adicionais.py::TestEntregaAutomatica::test_verificar_entregas_automaticas"
]

print("=" * 80)
print("EXECUTANDO TESTES QUE FALHARAM ANTERIORMENTE")
print("=" * 80)

comando = [sys.executable, "-m", "pytest"] + testes_para_correr + ["-v", "--tb=short"]

try:
    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    print(resultado.stdout)
    
    if resultado.stderr:
        print("ERROS:")
        print(resultado.stderr)
    
    print("\n" + "=" * 80)
    print(f"CÓDIGO DE SAÍDA: {resultado.returncode}")
    print("=" * 80)
    
except Exception as e:
    print(f"Erro ao executar testes: {str(e)}")
