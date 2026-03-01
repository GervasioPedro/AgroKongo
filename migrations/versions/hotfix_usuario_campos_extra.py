"""Hotfix: adicionar colunas extras em usuarios (produtor/comprador/auditoria)

Revision ID: hotfix_usuario_campos_extra
Revises: hotfix_usuario_senha_column
Create Date: 2026-02-28

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'hotfix_usuario_campos_extra'
down_revision = 'hotfix_usuario_senha_column'
branch_labels = None
depends_on = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table(table_name):
        return

    existing_cols = {c['name'] for c in inspector.get_columns(table_name)}
    if column.name in existing_cols:
        return

    try:
        op.add_column(table_name, column)
    except Exception:
        # Idempotência: se falhar (coluna já existe / limitação do dialect), não quebra o upgrade.
        pass


def upgrade():
    # Campos adicionais para produtores
    _add_column_if_missing('usuarios', sa.Column('principal_cultura', sa.String(length=100), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('experiencia_anos', sa.Integer(), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('certificacoes', sa.Text(), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('localizacao_fazenda', sa.String(length=255), nullable=True))

    # Campos para compradores
    _add_column_if_missing('usuarios', sa.Column('preferencias_compra', sa.Text(), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('limite_credito', sa.Numeric(14, 2), nullable=True))

    # Campos de auditoria
    _add_column_if_missing('usuarios', sa.Column('ultimo_login', sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('ip_ultimo_login', sa.String(length=45), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('ativo', sa.Boolean(), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('data_bloqueio', sa.DateTime(timezone=True), nullable=True))
    _add_column_if_missing('usuarios', sa.Column('motivo_bloqueio', sa.Text(), nullable=True))


def downgrade():
    # Downgrade conservador: não removemos colunas para evitar perda de dados.
    pass
