"""
Script para atualizar imports dos modelos antigos para novos
"""
import os
import re

# Mapeamento de imports antigos para novos
REPLACEMENTS = [
    # models_carteiras
    (r'from app\.models_carteiras import (.+)', r'from app.models import \1'),
    # models_disputa
    (r'from app\.models_disputa import (.+)', r'from app.models import \1'),
    # models_atualizado (se existir)
    (r'from app\.models_atualizado import (.+)', r'from app.models import \1'),
]

def atualizar_arquivo(filepath):
    """Atualiza imports em um arquivo"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        conteudo_original = conteudo
        
        # Aplicar todas as substituições
        for pattern, replacement in REPLACEMENTS:
            conteudo = re.sub(pattern, replacement, conteudo)
        
        # Se houve mudanças, salvar
        if conteudo != conteudo_original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            return True
        return False
    except Exception as e:
        print(f"Erro em {filepath}: {e}")
        return False

def main():
    """Processa todos os arquivos Python"""
    arquivos_atualizados = []
    
    # Percorrer app/
    for root, dirs, files in os.walk('app'):
        # Ignorar a pasta models/ (já está correta)
        if 'models' in dirs and root == 'app':
            dirs.remove('models')
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if atualizar_arquivo(filepath):
                    arquivos_atualizados.append(filepath)
    
    # Percorrer tests/
    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if atualizar_arquivo(filepath):
                    arquivos_atualizados.append(filepath)
    
    print(f"\nAtualizacao concluida!")
    print(f"{len(arquivos_atualizados)} arquivos atualizados:\n")
    for arquivo in arquivos_atualizados:
        print(f"  - {arquivo}")
    
    if not arquivos_atualizados:
        print("Nenhum arquivo precisou ser atualizado")

if __name__ == '__main__':
    main()
