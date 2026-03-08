# Script para executar testes de integração
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 
     'tests/integration/test_database_integration.py', 
     '-v', '--tb=short'],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
