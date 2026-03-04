#!/usr/bin/env python3
import os
import shutil
from datetime import datetime

def backup_file(filepath):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"[OK] Backup: {backup_path}")
    return backup_path

def apply_fix(original_file, fixed_file):
    if not os.path.exists(fixed_file):
        print(f"[ERRO] Arquivo nao encontrado: {fixed_file}")
        return False
    
    if not os.path.exists(original_file):
        print(f"[ERRO] Arquivo original nao encontrado: {original_file}")
        return False
    
    backup_file(original_file)
    shutil.copy2(fixed_file, original_file)
    print(f"[OK] Correcao aplicada: {original_file}")
    return True

def main():
    print("="*60)
    print("AGROKONGO - APLICADOR DE CORRECOES CRITICAS")
    print("="*60)
    print()
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    routes_path = os.path.join(base_path, "app", "routes")
    
    fixes = [
        {
            "name": "Protecao CSRF e Validacao de Entrada",
            "original": os.path.join(routes_path, "auth.py"),
            "fixed": os.path.join(routes_path, "auth_fixed.py"),
        },
        {
            "name": "Path Traversal, XSS e Open Redirect",
            "original": os.path.join(routes_path, "main.py"),
            "fixed": os.path.join(routes_path, "main_fixed.py"),
        },
        {
            "name": "Autorizacao e CSRF em Admin",
            "original": os.path.join(routes_path, "admin.py"),
            "fixed": os.path.join(routes_path, "admin_fixed.py"),
        }
    ]
    
    applied = 0
    failed = 0
    
    for fix in fixes:
        print(f"\n[*] {fix['name']}")
        if apply_fix(fix['original'], fix['fixed']):
            applied += 1
        else:
            failed += 1
    
    print()
    print("="*60)
    print(f"RESUMO: {applied} correcoes aplicadas, {failed} falhas")
    print("="*60)
    
    if failed == 0:
        print("\n[OK] TODAS AS CORRECOES FORAM APLICADAS COM SUCESSO!")
        return 0
    else:
        print(f"\n[ERRO] {failed} correcao(oes) falharam.")
        return 1

if __name__ == "__main__":
    exit(main())
