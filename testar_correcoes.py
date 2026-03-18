"""
Script para testar correcoes dos testes
"""
import sys
import subprocess

# Lista de testes que falharam
testes_falhos = [
    "tests/integration/test_api.py::TestApiSafras::test_detalhar_safra_nao_existente",
    "tests/integration/test_correcoes.py::TestRecusarReservaFix::test_recusar_reserva_repoe_stock",
    "tests/integration/test_fluxos_adicionais.py::TestRecusarReserva::test_recusar_reserva_repoe_stock",
    "tests/integration/test_fluxos_adicionais.py::TestRecusarReserva::test_recusar_reserva_apenas_pendente",
    "tests/integration/test_fluxos_adicionais.py::TestValidacoesSegurancaCompra::test_auto_compra_bloqueada",
    "tests/integration/test_fluxos_adicionais.py::TestValidacoesSegurancaCompra::test_compra_quantidade_indisponivel",
    "tests/integration/test_fluxos_adicionais.py::TestValidacoesSegurancaCompra::test_compra_quantidade_zero_negativa",
    "tests/integration/test_fluxos_adicionais.py::TestEntregaAutomatica::test_verificar_entregas_automaticas",
    "tests/unit/test_services.py::TestUsuarioService::test_validar_usuario_sucesso",
    "tests/unit/test_services.py::TestUsuarioService::test_rejeitar_usuario_com_motivo",
    "tests/integration/test_fluxo_escrow.py::TestFluxoEscrowCompleto::test_fluxo_completo_escrow",
    "tests/integration/test_fluxo_escrow.py::TestFluxoEscrowCompleto::test_recusar_reserva_repoe_stock",
    "tests/integration/test_fluxo_escrow.py::TestFluxoEscrowCompleto::test_validacoes_seguranca_compra"
]

print("=" * 80)
print("EXECUTANDO TESTES QUE FALHARAM...")
print("=" * 80)

# Executar pytest com os testes especÃ­ficos
cmd = ["python", "-m", "pytest"] + testes_falhos + ["-v", "--tb=short"]
result = subprocess.run(cmd, capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("\nERROS:\n")
    print(result.stderr)

print("\n" + "=" * 80)
print(f"CÃ“DIGO DE SAÃDA: {result.returncode}")
print("=" * 80)

sys.exit(result.returncode)
