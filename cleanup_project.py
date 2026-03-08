import os
import glob

def cleanup():
    # Lista de ficheiros exatos a remover
    files_to_remove = [
        "app/routes/comprador_v2.py",
        "app/routes/comprador_api.py",
        "app/routes/comprador_fixed.py",
        "app/routes/produtor_fixed.py",
        "app/routes/mercado_fixed.py",
        "app/routes/disputas_fixed.py",
        "app/routes/main_fixed.py",
        "app/routes/legacy_redirects.py" # Se já não for usado
    ]

    # Padrões para remover backups
    patterns = [
        "app/routes/*.backup*",
        "app/models/*.backup*",
        "*.tmp"
    ]

    print("Iniciando limpeza...")

    # Remover ficheiros específicos
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removido: {file_path}")
            except Exception as e:
                print(f"Erro ao remover {file_path}: {e}")
        else:
            print(f"Não encontrado (já removido?): {file_path}")

    # Remover padrões
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                print(f"Removido backup: {file_path}")
            except Exception as e:
                print(f"Erro ao remover {file_path}: {e}")

    print("Limpeza concluída.")

if __name__ == "__main__":
    cleanup()
