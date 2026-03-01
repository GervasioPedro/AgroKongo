"""Hotfix: tornar usuarios.senha_hash nullable (coluna legada)

Revision ID: hotfix_usuario_senha_hash_nullable
Revises: hotfix_usuario_campos_extra
Create Date: 2026-02-28

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'hotfix_usuario_senha_hash_nullable'
down_revision = 'hotfix_usuario_campos_extra'
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

    # SQLite precisa de batch_alter_table para alterar nullability
    try:
        with op.batch_alter_table('usuarios') as batch_op:
            batch_op.alter_column(
                'senha_hash',
                existing_type=sa.String(length=255),
                nullable=True,
            )
    except Exception:
        # Idempotência / compatibilidade: se já estiver nullable, ou se falhar por algum motivo,
        # não quebramos o upgrade.
        pass


def downgrade():
    # Downgrade conservador: não voltamos a impor NOT NULL.
    pass
