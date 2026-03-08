"""Limpa cache e executa testes automaticamente"""
import os
import shutil
import subprocess

def limpar_cache():
    """Remove todos os __pycache__"""
    print("🧹 Limpando cache...")
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            try:
                shutil.rmtree(os.path.join(root, '__pycache__'))
            except:
                pass
    print("✅ Cache limpo!\n")

if __name__ == "__main__":
    limpar_cache()
    print("🚀 Executando testes...\n")
    os.system("python -m pytest tests/automation/test_base_task_handler.py -v --tb=short")
