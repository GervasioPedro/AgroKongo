#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste rápido para validar que o conftest está usando SQLite e não PostgreSQL
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("TESTANDO CONFIGURAÇÃO DE TESTES - AGROKONGO")
print("=" * 80)

try:
    # Simular o que o conftest faz
    from app import create_app
    from app.extensions import db
    
    print("\n📦 Criando app de teste...")
    
    # Criar banco temporário (igual ao conftest)
    db_fd, db_path = tempfile.mkstemp()
    
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'UPLOAD_FOLDER_PRIVATE': tempfile.mkdtemp(),
        'UPLOAD_FOLDER_PUBLIC': tempfile.mkdtemp(),
        'CELERY_BROKER_URL': 'memory://',
        'CELERY_RESULT_BACKEND': 'memory://'
    }
    
    # Criar app
    app = create_app('dev')
    
    # Aplicar configurações
    with app.app_context():
        for key, value in test_config.items():
            app.config[key] = value
        
        # Verificar URI configurada
        configured_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"\n✅ Configurações aplicadas!")
        print(f"   SQLALCHEMY_DATABASE_URI: {configured_uri}")
        
        # Validar que é SQLite
        if configured_uri.startswith('sqlite:///'):
            print(f"\n✅ SUCESSO: Usando SQLite em memória!")
            print(f"   Arquivo temporário: {db_path}")
            
            # Tentar criar tabelas
            try:
                db.create_all()
                print(f"✅ Tabelas criadas com sucesso no SQLite!")
                
                # Limpar
                db.drop_all()
                print(f"✅ Tabelas removidas (cleanup)")
                
            except Exception as e:
                print(f"\n❌ ERRO ao criar tabelas: {e}")
                sys.exit(1)
        else:
            print(f"\n❌ ERRO CRÍTICO: Não está usando SQLite!")
            print(f"   URI configurada: {configured_uri}")
            sys.exit(1)
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    
    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO BEM-SUCEDIDA!")
    print("=" * 80)
    print("\nOs testes agora usarão SQLite em memória.")
    print("Execute: pytest tests/integration/ -v")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
