"""Script para limpar cache e executar testes"""
import os
import shutil
import subprocess
import sys

def limpar_cache():
    """Limpa todos os diretórios __pycache__"""
    print("🧹 Limpando cache...")
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"  ✓ {pycache_path}")
            except Exception as e:
                print(f"  ✗ Erro em {pycache_path}: {e}")
    
    # Limpar arquivos .pyc também
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                except Exception as e:
                    pass
    
    print("✅ Cache limpo!\n")

def executar_testes():
    """Executa os testes"""
    print("🚀 Executando testes...\n")
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/automation/test_base_task_handler.py",
        "-v",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode

if __name__ == "__main__":
    limpar_cache()
    codigo_retorno = executar_testes()
    sys.exit(codigo_retorno)
