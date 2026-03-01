"""Hotfix v2: garantir usuarios.senha_hash nullable (SQLite recriar tabela)

Revision ID: hotfix_usuario_senha_hash_nullable_v2
Revises: hotfix_usuario_senha_hash_nullable
Create Date: 2026-02-28

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'hotfix_usuario_senha_hash_nullable_v2'
down_revision = 'hotfix_usuario_senha_hash_nullable'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table('usuarios'):
        return

    cols = {c['name'] for c in inspector.get_columns('usuarios')}
    if 'senha_hash' not in cols:
        return

    # Em SQLite, alterar NOT NULL muitas vezes exige recriar a tabela.
    try:
        with op.batch_alter_table('usuarios', recreate='always') as batch_op:
            batch_op.alter_column(
                'senha_hash',
                existing_type=sa.String(length=255),
                nullable=True,
            )
    except Exception:
        pass


def downgrade():
    # Downgrade conservador: não voltamos a impor NOT NULL.
    pass
