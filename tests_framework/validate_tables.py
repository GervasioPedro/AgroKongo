"""
Script para validar criação das tabelas de teste
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
from sqlalchemy import inspect

# IMPORTAR TODOS OS MODELOS
from app.models import (
    Usuario, Provincia, Municipio, Produto, Safra,
    Transacao, HistoricoStatus, Avaliacao, Notificacao,
    AlertaPreferencia, Disputa, LogAuditoria, ConfiguracaoSistema,
    ConsentimentoLGPD, RegistroAnonimizacao,
)
from app.models.financeiro import Carteira, MovimentacaoFinanceira

print("=" * 80)
print("VALIDANDO CRIAÇÃO DAS TABELAS")
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
    
    # Verificar se as tabelas foram criadas
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\n✅ Tabelas criadas: {len(tables)}")
    for table in sorted(tables):
        print(f"   - {table}")
    
    # Verificar tabelas esperadas
    expected_tables = [
        'usuarios', 'provincias', 'municipios', 'produtos', 'safras',
        'transacoes', 'historicos_status', 'avaliacoes', 'notificacoes',
        'alertas_preferencia', 'disputas', 'logs_auditoria', 'configuracoes_sistema',
        'consentimentos_lgpd', 'registros_anonimizacao',
        'carteiras', 'movimentacoes_financeiras'
    ]
    
    print("\n" + "=" * 80)
    print("VERIFICANDO TABELAS CRÍTICAS")
    print("=" * 80)
    
    missing = []
    for table in expected_tables:
        if table in tables:
            print(f"✅ {table}")
        else:
            print(f"❌ {table} FALTANTE!")
            missing.append(table)
    
    if missing:
        print(f"\n❌ ERRO: {len(missing)} tabelas faltantes!")
        sys.exit(1)
    else:
        print(f"\n✅ SUCESSO: Todas as {len(expected_tables)} tabelas críticas foram criadas!")
        sys.exit(0)
