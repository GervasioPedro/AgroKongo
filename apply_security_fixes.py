#!/usr/bin/env python3
"""
Script para aplicar correções críticas de segurança ao AgroKongo
Uso: python apply_security_fixes.py
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """Cria backup de um arquivo"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{filepath}.backup_{timestamp}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    return backup_path

def apply_fix(original_file, fixed_file):
    """Aplica uma correção de segurança"""
    if not os.path.exists(fixed_file):
        print(f"❌ Arquivo corrigido não encontrado: {fixed_file}")
        return False
    
    if not os.path.exists(original_file):
        print(f"❌ Arquivo original não encontrado: {original_file}")
        return False
    
    # Criar backup
    backup_file(original_file)
    
    # Aplicar correção
    shutil.copy2(fixed_file, original_file)
    print(f"✅ Correção aplicada: {original_file}")
    return True

def main():
    print("=" * 60)
    print("🔒 AGROKONGO - APLICADOR DE CORREÇÕES CRÍTICAS DE SEGURANÇA")
    print("=" * 60)
    print()
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    routes_path = os.path.join(base_path, "app", "routes")
    
    fixes = [
        {
            "name": "Proteção CSRF e Validação de Entrada",
            "original": os.path.join(routes_path, "auth.py"),
            "fixed": os.path.join(routes_path, "auth_fixed.py"),
            "cwe": "CWE-352, CWE-400"
        },
        {
            "name": "Path Traversal, XSS e Open Redirect",
            "original": os.path.join(routes_path, "main.py"),
            "fixed": os.path.join(routes_path, "main_fixed.py"),
            "cwe": "CWE-22, CWE-79, CWE-601"
        },
        {
            "name": "Autorização e CSRF em Admin",
            "original": os.path.join(routes_path, "admin.py"),
            "fixed": os.path.join(routes_path, "admin_fixed.py"),
            "cwe": "CWE-352, CWE-862"
        }
    ]
    
    applied = 0
    failed = 0
    
    for fix in fixes:
        print(f"\n📋 {fix['name']}")
        print(f"   CWE: {fix['cwe']}")
        print(f"   Original: {fix['original']}")
        print(f"   Corrigido: {fix['fixed']}")
        
        if apply_fix(fix['original'], fix['fixed']):
            applied += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"📊 RESUMO: {applied} correções aplicadas, {failed} falhas")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ TODAS AS CORREÇÕES FORAM APLICADAS COM SUCESSO!")
        print("\n📝 Próximos passos:")
        print("   1. Executar testes de regressão")
        print("   2. Verificar logs de erro")
        print("   3. Testar fluxo de login")
        print("   4. Testar upload de arquivos")
        print("   5. Validar em produção")
        print("\n🔐 Vulnerabilidades corrigidas:")
        print("   • CWE-352: Missing CSRF Protection")
        print("   • CWE-22: Path Traversal")
        print("   • CWE-79: Cross-Site Scripting (XSS)")
        print("   • CWE-601: Open Redirect")
        print("   • CWE-862: Missing Authorization")
        print("   • CWE-400: Uncontrolled Resource Consumption")
    else:
        print(f"\n❌ {failed} correção(ões) falharam. Verifique os caminhos dos arquivos.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
