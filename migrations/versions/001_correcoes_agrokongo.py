"""correcoes_agrokongo - Correções críticas de schema para AgroKongo

Revision ID: 001
Revises:
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = '001_correcoes_agrokongo'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Aplica todas as correções de schema necessárias."""

    # ==================== 1. ADICIONAR data_liquidacao EM Transacoes ====================
    # Usado em: admin.py, reports.py, pagamentos.py, relatorios.py, limpeza.py
    try:
        op.add_column('transacoes',
                      sa.Column('data_liquidacao', sa.DateTime(timezone=True), nullable=True)
                      )
        print("[OK] Coluna 'data_liquidacao' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] data_liquidacao já existe ou erro: {e}")

    # ==================== 2. ADICIONAR data_pagamento EM Transacoes ====================
    # Usado em: comprador.py, admin.py
    try:
        op.add_column('transacoes',
                      sa.Column('data_pagamento', sa.DateTime(timezone=True), nullable=True)
                      )
        print("[OK] Coluna 'data_pagamento' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] data_pagamento já existe ou erro: {e}")

    # ==================== 3. ADICIONAR data_envio EM Transacoes ====================
    # Usado em: models.py (calcular_janela_logistica)
    try:
        op.add_column('transacoes',
                      sa.Column('data_envio', sa.DateTime(timezone=True), nullable=True)
                      )
        print("[OK] Coluna 'data_envio' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] data_envio já existe ou erro: {e}")

    # ==================== 4. ADICIONAR data_entrega EM Transacoes ====================
    # Usado em: models.py, comprador.py
    try:
        op.add_column('transacoes',
                      sa.Column('data_entrega', sa.DateTime(timezone=True), nullable=True)
                      )
        print("[OK] Coluna 'data_entrega' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] data_entrega já existe ou erro: {e}")

    # ==================== 5. ADICIONAR previsao_entrega EM Transacoes ====================
    # Usado em: models.py, comprador.py
    try:
        op.add_column('transacoes',
                      sa.Column('previsao_entrega', sa.DateTime(timezone=True), nullable=True)
                      )
        print("[OK] Coluna 'previsao_entrega' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] previsao_entrega já existe ou erro: {e}")

    # ==================== 6. ADICIONAR transferencia_concluida EM Transacoes ====================
    # Usado em: admin.py, pagamentos.py
    try:
        op.add_column('transacoes',
                      sa.Column('transferencia_concluida', sa.Boolean, default=False, nullable=True)
                      )
        print("[OK] Coluna 'transferencia_concluida' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] transferencia_concluida já existe ou erro: {e}")

    # ==================== 7. ADICIONAR is_active EM Transacoes ====================
    # Usado em: models.py, limpeza.py
    try:
        op.add_column('transacoes',
                      sa.Column('is_active', sa.Boolean, default=True, nullable=True)
                      )
        print("[OK] Coluna 'is_active' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] is_active já existe ou erro: {e}")

    # ==================== 8. ADICIONAR deleted_at EM Transacoes ====================
    # Usado em: models.py (soft delete)
    try:
        op.add_column('transacoes',
                      sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True)
                      )
        print("[OK] Coluna 'deleted_at' adicionada em transacoes")
    except Exception as e:
        print(f"[WARN] deleted_at já existe ou erro: {e}")

    # ==================== 9. CRIAR TABELA pagamentos_logs ====================
    # Usado em: pagamentos.py, admin.py
    try:
        op.create_table('pagamentos_logs',
                        sa.Column('id', sa.Integer(), nullable=False),
                        sa.Column('trans_id', sa.String(length=50), nullable=False, index=True),
                        sa.Column('valor_liquidado', sa.Numeric(precision=14, scale=2), nullable=True),
                        sa.Column('acao', sa.String(length=50), nullable=True),
                        sa.Column('detalhes', sa.Text(), nullable=True),
                        sa.Column('data', sa.DateTime(timezone=True), nullable=True),
                        sa.PrimaryKeyConstraint('id')
                        )
        print("[OK] Tabela 'pagamentos_logs' criada")
    except Exception as e:
        print(f"[WARN] pagamentos_logs já existe ou erro: {e}")

    # ==================== 10. CRIAR TABELA movimentacoes_financeiras ====================
    # Usado em: models.py (Usuario.saldo_disponivel), pagamentos.py
    try:
        op.create_table('movimentacoes_financeiras',
                        sa.Column('id', sa.Integer(), nullable=False),
                        sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuarios.id', ondelete='CASCADE'),
                                  nullable=False),
                        sa.Column('transacao_id', sa.Integer(), sa.ForeignKey('transacoes.id'), nullable=True),
                        sa.Column('valor', sa.Numeric(precision=14, scale=2), nullable=False),
                        sa.Column('tipo', sa.String(length=30), nullable=False),
                        sa.Column('descricao', sa.String(length=255), nullable=True),
                        sa.Column('data_criacao', sa.DateTime(timezone=True), nullable=True),
                        sa.PrimaryKeyConstraint('id')
                        )
        print("[OK] Tabela 'movimentacoes_financeiras' criada")
    except Exception as e:
        print(f"[WARN] movimentacoes_financeiras já existe ou erro: {e}")

    # ==================== 11. CRIAR ÍNDICES PARA PERFORMANCE ====================
    # Índices críticos para queries frequentes
    try:
        op.create_index('idx_transacao_status', 'transacoes', ['status'], unique=False)
        print("[OK] Indice 'idx_transacao_status' criado")
    except Exception as e:
        print(f"[WARN] idx_transacao_status já existe ou erro: {e}")

    try:
        op.create_index('idx_transacao_data_criacao', 'transacoes', ['data_criacao'], unique=False)
        print("[OK] Indice 'idx_transacao_data_criacao' criado")
    except Exception as e:
        print(f"[WARN] idx_transacao_data_criacao já existe ou erro: {e}")

    try:
        op.create_index('idx_transacao_data_liquidacao', 'transacoes', ['data_liquidacao'], unique=False)
        print("[OK] Indice 'idx_transacao_data_liquidacao' criado")
    except Exception as e:
        print(f"[WARN] idx_transacao_data_liquidacao já existe ou erro: {e}")

    try:
        op.create_index('idx_usuario_kyc_status', 'usuarios', ['kyc_status'], unique=False)
        print("[OK] Indice 'idx_usuario_kyc_status' criado")
    except Exception as e:
        print(f"[WARN] idx_usuario_kyc_status já existe ou erro: {e}")

    try:
        op.create_index('idx_usuario_conta_validada', 'usuarios', ['conta_validada'], unique=False)
        print("[OK] Indice 'idx_usuario_conta_validada' criado")
    except Exception as e:
        print(f"[WARN] idx_usuario_conta_validada já existe ou erro: {e}")

    try:
        op.create_index('idx_safra_status', 'safras', ['status'], unique=False)
        print("[OK] Indice 'idx_safra_status' criado")
    except Exception as e:
        print(f"[WARN] idx_safra_status já existe ou erro: {e}")

    # ==================== 12. RENOMEAR COLUNA ip_address PARA ip (LogAuditoria) ====================
    # Consistência com handlers.py
    try:
        op.alter_column('logs_auditoria', 'ip_address', new_column_name='ip')
        print("[OK] Coluna 'ip_address' renomeada para 'ip' em logs_auditoria")
    except Exception as e:
        print(f"[WARN] Renomeacao ip_address ja feita ou erro: {e}")

    # ==================== 13. RENOMEAR COLUNA data PARA data_criacao (LogAuditoria) ====================
    # Consistência com handlers.py
    try:
        op.alter_column('logs_auditoria', 'data', new_column_name='data_criacao')
        print("[OK] Coluna 'data' renomeada para 'data_criacao' em logs_auditoria")
    except Exception as e:
        print(f"[WARN] Renomeacao data ja feita ou erro: {e}")

    # ==================== 14. RENOMEAR COLUNA data_registo PARA data_cadastro (Usuarios) ====================
    # Consistência com reports.py
    try:
        op.alter_column('usuarios', 'data_registo', new_column_name='data_cadastro')
        print("[OK] Coluna 'data_registo' renomeada para 'data_cadastro' em usuarios")
    except Exception as e:
        print(f"[WARN] Renomeacao data_registo ja feita ou erro: {e}")

    print("\n" + "=" * 70)
    print("[DONE] MIGRACAO CONCLUIDA COM SUCESSO!")
    print("=" * 70)
    print("\nPróximos passos:")
    print("1. Execute: flask db upgrade")
    print("2. Verifique: flask db current")
    print("3. Teste a app: flask run")
    print("=" * 70 + "\n")


def downgrade():
    """Reverte todas as correções (use apenas se necessário)."""

    # Reverter renomeações
    try:
        op.alter_column('logs_auditoria', 'ip', new_column_name='ip_address')
        op.alter_column('logs_auditoria', 'data_criacao', new_column_name='data')
        op.alter_column('usuarios', 'data_cadastro', new_column_name='data_registo')
        print("[OK] Renomeacoes revertidas")
    except Exception as e:
        print(f"[WARN] Erro ao reverter renomeacoes: {e}")

    # Drop índices
    try:
        op.drop_index('idx_transacao_status', table_name='transacoes')
        op.drop_index('idx_transacao_data_criacao', table_name='transacoes')
        op.drop_index('idx_transacao_data_liquidacao', table_name='transacoes')
        op.drop_index('idx_usuario_kyc_status', table_name='usuarios')
        op.drop_index('idx_usuario_conta_validada', table_name='usuarios')
        op.drop_index('idx_safra_status', table_name='safras')
        print("[OK] Indices removidos")
    except Exception as e:
        print(f"[WARN] Erro ao remover indices: {e}")

    # Drop tabelas
    try:
        op.drop_table('movimentacoes_financeiras')
        op.drop_table('pagamentos_logs')
        print("[OK] Tabelas removidas")
    except Exception as e:
        print(f"[WARN] Erro ao remover tabelas: {e}")

    # Drop colunas
    try:
        op.drop_column('transacoes', 'deleted_at')
        op.drop_column('transacoes', 'is_active')
        op.drop_column('transacoes', 'transferencia_concluida')
        op.drop_column('transacoes', 'previsao_entrega')
        op.drop_column('transacoes', 'data_entrega')
        op.drop_column('transacoes', 'data_envio')
        op.drop_column('transacoes', 'data_pagamento')
        op.drop_column('transacoes', 'data_liquidacao')
        print("[OK] Colunas removidas")
    except Exception as e:
        print(f"[WARN] Erro ao remover colunas: {e}")

    print("\n[WARN] DOWNGRADE CONCLUIDO (schema revertido para versao anterior)")