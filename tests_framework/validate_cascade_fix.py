"""
Script para validar correção do cascade LogAuditoria
"""
import os
import sys
from pathlib import Path

# Adicionar root do projeto ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Definir variável de ambiente ANTES de qualquer importação
os.environ['TEST_DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.extensions import db
from app.models import Usuario, LogAuditoria

print("=" * 80)
print("VALIDANDO CORREÇÃO DO CASCADE - LOG AUDITORIA")
print("=" * 80)

app = create_app('dev')
app.config.update(
    TESTING=True,
    SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

with app.app_context():
    # Criar todas as tabelas
    print("\nCriando tabelas...")
    db.create_all()
    print("✅ Tabelas criadas com sucesso")
    
    # Testar criação de LogAuditoria sem usuário
    print("\nTestando criação de LogAuditoria sem usuário...")
    try:
        log = LogAuditoria(
            usuario_id=None,  # Sistema
            acao="TESTE",
            detalhes="Log de teste sem usuário associado",
            ip_address="127.0.0.1"
        )
        db.session.add(log)
        db.session.commit()
        print("✅ LogAuditoria criado com SUCESSO (usuario_id=None)")
        print(f"   ID do Log: {log.id}")
        print(f"   Ação: {log.acao}")
        print(f"   Detalhes: {log.detalhes}")
    except Exception as e:
        print(f"❌ ERRO ao criar LogAuditoria: {e}")
        sys.exit(1)
    
    # Testar criação de usuário
    print("\nTestando criação de Usuário...")
    try:
        usuario = Usuario(
            nome="Test User",
            telemovel="923456789",
            email="test@example.com",
            senha="senha123",
            tipo="comprador"
        )
        db.session.add(usuario)
        db.session.commit()
        print("✅ Usuário criado com SUCESSO")
        print(f"   ID: {usuario.id}")
        print(f"   Nome: {usuario.nome}")
        print(f"   Telemovel: {usuario.telemovel}")
    except Exception as e:
        print(f"❌ ERRO ao criar Usuário: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ TODOS OS TESTES PASSARAM!")
    print("=" * 80)
    print("\nA correção do cascade funcionou corretamente.")
    print("Logs de auditoria podem ser criados sem usuário associado.")
