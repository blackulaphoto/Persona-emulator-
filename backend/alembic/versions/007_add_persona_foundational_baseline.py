"""add persona foundational baseline fields

Revision ID: 007_add_foundational_baseline
Revises: 6e28795dc8ca
Create Date: 2025-12-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic. Shortened from
# '007_add_persona_foundational_baseline' (37 chars) - alembic_version.
# version_num is a hardcoded VARCHAR(32) with no config hook to widen it
# (see alembic.ddl.impl.DefaultImpl.version_table_impl); SQLite never
# enforced that length, Postgres does (StringDataRightTruncation), so any
# revision id over 32 chars only ever worked by accident on SQLite. Every
# revision id in this project exceeding 32 chars is shortened the same way
# in this change - see the sibling revisions this touches.
revision: str = '007_add_foundational_baseline'
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
                # sa.text('0') compiles to a bare integer literal, which
                # SQLite accepts for a boolean-affinity column but Postgres
                # rejects (DatatypeMismatch: column is boolean, default
                # expression is integer). sa.false() is the dialect-agnostic
                # construct - compiles to `0` for SQLite and `false` for
                # Postgres automatically. Confirmed failing against real
                # Postgres before this fix; confirmed passing after.
                server_default=sa.false()
            )
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('personas') as batch:
        batch.drop_column('baseline_initialized')
        batch.drop_column('foundational_environment_signals')
