"""add persona foundational baseline fields

Revision ID: 007_add_persona_foundational_baseline
Revises: 6e28795dc8ca
Create Date: 2025-12-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_add_persona_foundational_baseline'
down_revision: Union[str, Sequence[str], None] = '6e28795dc8ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('personas') as batch:
        batch.add_column(
            sa.Column(
                'foundational_environment_signals',
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'")
            )
        )
        batch.add_column(
            sa.Column(
                'baseline_initialized',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('0')
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('personas') as batch:
        batch.drop_column('baseline_initialized')
        batch.drop_column('foundational_environment_signals')
