"""Script para validar correção do erro de coleta"""
import subprocess
import sys

print("=" * 80)
print("VALIDANDO CORREÇÃO DO ERRO DE COLETA")
print("=" * 80)

# Testar apenas o arquivo problemático
result = subprocess.run([
    sys.executable, "-m", "pytest",
    "tests/unit/test_cadastro_produtor.py::TestOTPService",
    "-v", "--tb=short"
], capture_output=True, text=True)

print("\nSTDOUT:")
print(result.stdout)

if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

print("\n" + "=" * 80)
print(f"CÓDIGO DE RETORNO: {result.returncode}")
print("=" * 80)

if result.returncode == 0:
    print("✅ SUCESSO! Erro de coleta foi resolvido!")
else:
    print("❌ ERRO PERSISTE!")
    
# Salvar output em arquivo
with open("erros_atualizado.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    if result.stderr:
        f.write("\nSTDERR:\n")
        f.write(result.stderr)

print("\nResultado salvo em 'erros_atualizado.txt'")
