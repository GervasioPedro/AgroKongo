"""Hotfix: alinhar coluna de senha do Usuario (senha vs senha_hash)

Revision ID: hotfix_usuario_senha_column
Revises: merge_fix_safras_cols
Create Date: 2026-02-28

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'hotfix_usuario_senha_column'
down_revision = 'merge_fix_safras_cols'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table('usuarios'):
        return

    cols = {c['name'] for c in inspector.get_columns('usuarios')}

    # Se já existe 'senha', não faz nada.
    if 'senha' not in cols:
        try:
            op.add_column('usuarios', sa.Column('senha', sa.String(length=255), nullable=True))
        except Exception:
            pass

    # Backfill: copiar senha_hash -> senha para registos existentes
    # (mantemos senha_hash para compatibilidade retroativa)
    cols = {c['name'] for c in inspector.get_columns('usuarios')}
    if 'senha' in cols and 'senha_hash' in cols:
        try:
            op.execute(sa.text("UPDATE usuarios SET senha = senha_hash WHERE senha IS NULL OR senha = ''"))
        except Exception:
            pass

    # Se existir email duplicado e índice unique, este update não mexe em email, por isso é seguro.


def downgrade():
    # Downgrade conservador: não removemos a coluna para não perder dados.
    pass
