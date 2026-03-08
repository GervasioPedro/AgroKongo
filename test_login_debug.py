"""Teste rápido de autenticação Flask-Login"""
import tempfile
import os
from app import create_app, db
from app.models import Usuario

# Configurar app de teste
db_fd, db_path = tempfile.mkstemp()
test_config = {
    'TESTING': True,
    'WTF_CSRF_ENABLED': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SECRET_KEY': 'test-secret-key',
}

app = create_app('dev', test_config_override=test_config)

with app.app_context():
    db.create_all()
    
    # Criar admin
    admin = Usuario(
        nome="Admin Test",
        telemovel="923456789",
        email="admin@test.com",
        senha="123456",
        tipo="admin",
        conta_validada=True,
        perfil_completo=True
    )
    db.session.add(admin)
    db.session.commit()
    
    print(f"✅ Admin criado com ID: {admin.id}")
    
    # Testar load_user
    from app.models.usuario import load_user
    user_carregado = load_user(str(admin.id))
    print(f"✅ load_user funcionou: {user_carregado}")
    print(f"   - User ID: {user_carregado.id}")
    print(f"   - User tipo: {user_carregado.tipo}")
    print(f"   - is_authenticated: {user_carregado.is_authenticated}")
    
    # Testar sessão do cliente
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
            print(f"\n✅ Sessão configurada:")
            print(f"   - _user_id: {sess.get('_user_id')}")
            print(f"   - _fresh: {sess.get('_fresh')}")
        
        # Fazer requisição
        response = client.get('/admin/test')
        print(f"\n✅ Resposta da requisição:")
        print(f"   - Status code: {response.status_code}")
        print(f"   - Data: {response.data[:200] if response.data else 'None'}")
    
    db.drop_all()

os.close(db_fd)
os.unlink(db_path)
print("\n✅ Teste concluído!")
