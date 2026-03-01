"""Merge heads + hotfix colunas em safras

Revision ID: merge_fix_safras_cols
Revises: implementar_status_conta_carteiras, afef678e5fe9, 7a474bd9890e
Create Date: 2026-02-28

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_fix_safras_cols'
down_revision = ('implementar_status_conta_carteiras', 'afef678e5fe9', '7a474bd9890e')
branch_labels = None
depends_on = None


def _try_add_column(table_name: str, column: sa.Column):
    try:
        with op.batch_alter_table(table_name, schema=None) as batch_op:
            batch_op.add_column(column)
    except Exception:
        # Coluna já existe ou SQLite não permite a operação no estado atual
        pass


def upgrade():
    # Garantir compatibilidade com o modelo Safra atual (evita "no such column")
    _try_add_column('safras', sa.Column('descricao', sa.Text(), nullable=True))
    _try_add_column('safras', sa.Column('observacoes', sa.Text(), nullable=True))
    _try_add_column('safras', sa.Column('data_plantio', sa.Date(), nullable=True))
    _try_add_column('safras', sa.Column('data_previsao_colheita', sa.Date(), nullable=True))
    _try_add_column('safras', sa.Column('localizacao', sa.String(length=255), nullable=True))
    _try_add_column('safras', sa.Column('data_atualizacao', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    # Downgrade seguro: tenta remover apenas se existir
    for col in [
        'data_atualizacao',
        'localizacao',
        'data_previsao_colheita',
        'data_plantio',
        'observacoes',
        'descricao',
    ]:
        try:
            with op.batch_alter_table('safras', schema=None) as batch_op:
                batch_op.drop_column(col)
        except Exception:
            pass
