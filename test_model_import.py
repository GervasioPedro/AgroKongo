#!/usr/bin/env python
"""Teste rápido de importação dos modelos"""
import sys
sys.path.insert(0, '.')

# Limpar cache
import importlib
import os

print("🔍 Testando importação dos modelos...")

try:
    from app import create_app
    print("✅ create_app importado")
    
    with create_app().app_context():
        print("✅ Contexto da aplicação criado")
        
        from app.models import Usuario, Safra, Transacao
        print("✅ Modelos importados com sucesso")
        
        # Verificar relacionamentos
        print("\n📊 Verificando relacionamentos:")
        print(f"  Safra.transacoes: {Safra.transacoes}")
        print(f"  Transacao.safra: {Transacao.safra}")
        
        print("\n✅ TODOS OS MODELOS FUNCIONAM CORRETAMENTE!")
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
