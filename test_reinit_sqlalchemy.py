#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste para validar a correção do conftest - forçar re-inicialização do SQLAlchemy
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("TESTANDO RE-INICIALIZAÇÃO DO SQLALCHEMY - AGROKONGO")
print("=" * 80)

try:
    from app import create_app
    from app.extensions import db
    
    print("\n📦 Criando app com config 'dev' (que usa PostgreSQL)...")
    
    # Criar arquivo temporário para SQLite
    db_fd, db_path = tempfile.mkstemp()
    
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
    }
    
    # Criar app
    app = create_app('dev')
    
    # Aplicar configurações de teste
    print("📋 Aplicando configurações de teste...")
    for key, value in test_config.items():
        app.config[key] = value
    
    print(f"   URI configurada: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Entrar no contexto e re-inicializar
    with app.app_context():
        print("\n🔄 Re-inicializando SQLAlchemy...")
        
        # Dispor do engine antigo
        if 'sqlalchemy' in app.extensions:
            old_engine = app.extensions['sqlalchemy'].engine
            if old_engine is not None:
                print(f"   Descartando engine antigo: {old_engine.url}")
                old_engine.dispose()
        
        # Re-inicializar
        print("   Chamando db.init_app(app)...")
        db.init_app(app)
        
        # Verificar novo engine
        new_engine = db.engine
        print(f"   Novo engine URL: {new_engine.url}")
        
        if str(new_engine.url).startswith('sqlite'):
            print(f"\n✅ SUCESSO: Engine é SQLite!")
            
            # Tentar criar tabelas
            try:
                print("\n📦 Criando tabelas...")
                db.create_all()
                print(f"✅ Tabelas criadas com sucesso!")
                
                # Contar tabelas
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"   Total de tabelas criadas: {len(tables)}")
                
                # Limpar
                db.drop_all()
                print(f"✅ Tabelas removidas (cleanup)")
                
            except Exception as e:
                print(f"\n❌ ERRO ao criar tabelas: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)
        else:
            print(f"\n❌ ERRO CRÍTICO: Engine NÃO é SQLite!")
            print(f"   Engine URL: {new_engine.url}")
            sys.exit(1)
    
    # Cleanup
    try:
        os.close(db_fd)
        os.unlink(db_path)
    except:
        pass
    
    print("\n" + "=" * 80)
    print("✅ VALIDAÇÃO BEM-SUCEDIDA!")
    print("=" * 80)
    print("\nA re-inicialização do SQLAlchemy está funcionando.")
    print("Os testes agora usarão SQLite em memória.")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
