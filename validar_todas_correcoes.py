"""Script para validar TODAS as correções aplicadas"""
import subprocess
import sys

print("=" * 80)
print("VALIDANDO CORREÇÕES APLICADAS")
print("=" * 80)

# Testar o arquivo completo
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/unit/test_cadastro_produtor.py::TestOTPService",
    "-v", "--tb=line"
], capture_output=True, text=True)

print("\nRESULTADO DOS TESTES OTPService:")
print("-" * 80)
for line in result.stdout.split('\n'):
    if 'PASSED' in line or 'FAILED' in line or 'test_' in line:
        print(line)

print("\n" + "=" * 80)
print(f"CÓDIGO DE RETORNO: {result.returncode}")
print("=" * 80)

if result.returncode == 0:
    print("✅ SUCESSO! Todos os testes do OTPService passaram!")
else:
    print("❌ ALGUNS TESTES FALHARAM!")
    
# Salvar output em arquivo
with open("erros_atualizado.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\nSTDERR:\n")
        f.write(result.stderr)

print("\nResultado detalhado salvo em 'erros_atualizado.txt'")
