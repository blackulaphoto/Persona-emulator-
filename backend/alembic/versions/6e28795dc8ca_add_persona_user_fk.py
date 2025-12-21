"""add persona user fk

Revision ID: 6e28795dc8ca
Revises: add_user_id_columns
Create Date: 2025-12-20 18:47:49.159587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e28795dc8ca'
down_revision: Union[str, Sequence[str], None] = 'add_user_id_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('personas') as batch:
        batch.create_foreign_key(
            'fk_personas_user_id',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE',
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('personas') as batch:
        batch.drop_constraint('fk_personas_user_id', type_='foreignkey')
