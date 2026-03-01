#!/usr/bin/env python3
# run_migration_cadastro.py - Script para executar migração do cadastro
# Atualiza sistema para alinhar com caso de uso especificado

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_migrate import upgrade
from app import create_app, db
from app.models_carteiras import StatusConta

def main():
    """Executa migração do sistema de cadastro"""
    print("🌱 AgroKongo - Migração do Sistema de Cadastro")
    print("=" * 50)
    
    # Criar aplicação
    app = create_app()
    
    with app.app_context():
        try:
            print("📋 Executando migração: implementar_status_conta_carteiras")
            
            # Executar migration específica
            upgrade('implementar_status_conta_carteiras')
            
            print("✅ Migration executada com sucesso!")
            print("")
            
            # Verificar estados disponíveis
            print("📊 Estados de conta disponíveis:")
            for status, descricao in StatusConta.choices():
                print(f"   • {status}: {descricao}")
            
            print("")
            print("🎯 Próximos passos:")
            print("1. Substituir app/models.py por app/models_atualizado.py")
            print("2. Atualizar app/utils/decorators.py")
            print("3. Registrar novo blueprint em app/__init__.py")
            print("4. Testar fluxo de cadastro completo")
            print("")
            print("🚀 Sistema alinhado com caso de uso especificado!")
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            print("Verifique o log acima para detalhes.")
            sys.exit(1)

if __name__ == '__main__':
    main()
