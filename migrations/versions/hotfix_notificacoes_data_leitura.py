"""Hotfix: adicionar coluna notificacoes.data_leitura

Revision ID: hotfix_notificacoes_data_leitura
Revises: hotfix_usuario_senha_hash_nullable_v2
Create Date: 2026-02-28

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'hotfix_notificacoes_data_leitura'
down_revision = 'hotfix_usuario_senha_hash_nullable_v2'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table('notificacoes'):
        return

    cols = {c['name'] for c in inspector.get_columns('notificacoes')}
    if 'data_leitura' in cols:
        return

    try:
        op.add_column('notificacoes', sa.Column('data_leitura', sa.DateTime(timezone=True), nullable=True))
    except Exception:
        # Idempotência: se já existir / falhar por motivo de dialect, não quebra o upgrade.
        pass


def downgrade():
    # Downgrade conservador: não removemos coluna para evitar perda de dados.
    pass
