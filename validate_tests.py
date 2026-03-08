# Script de validação rápida dos testes
import subprocess
import sys

print("=" * 80)
print("VALIDANDO COLETA DE TESTES - AGROKONGO")
print("=" * 80)

# Testar coleta unitária
print("\n📋 Coletando testes unitários...")
result = subprocess.run(
    ["pytest", "tests/unit/", "--collect-only", "-q"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Testes unitários coletados com sucesso!")
    # Extrair número de testes
    for line in result.stdout.split('\n'):
        if 'test session starts' in line or 'collected' in line:
            print(f"   {line.strip()}")
else:
    print("❌ Erro na coleta de testes unitários:")
    print(result.stderr[:500])

# Testar coleta de integração
print("\n📋 Coletando testes de integração...")
result = subprocess.run(
    ["pytest", "tests/integration/", "--collect-only", "-q"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Testes de integração coletados com sucesso!")
    for line in result.stdout.split('\n'):
        if 'collected' in line:
            print(f"   {line.strip()}")
else:
    print("❌ Erro na coleta de testes de integração:")
    print(result.stderr[:500])

# Testar coleta de automação
print("\n📋 Coletando testes de automação...")
result = subprocess.run(
    ["pytest", "tests/automation/", "--collect-only", "-q"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Testes de automação coletados com sucesso!")
    for line in result.stdout.split('\n'):
        if 'collected' in line:
            print(f"   {line.strip()}")
else:
    print("❌ Erro na coleta de testes de automação:")
    print(result.stderr[:500])

print("\n" + "=" * 80)
print("VALIDAÇÃO CONCLUÍDA")
print("=" * 80)
