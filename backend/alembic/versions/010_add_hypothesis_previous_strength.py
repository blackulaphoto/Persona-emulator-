"""add clinical_pattern_hypotheses.previous_evidence_strength (Step 12)

Lets the persona board show a clinical-pattern hypothesis STRENGTHENING or
WEAKENING rather than only its current confidence number - `status`
(open/revised/dismissed) records whether a hypothesis was revisited, not
which direction it moved.

DEFENSIVE BY NECESSITY: clinical_pattern_hypotheses is one of the tables that
has never been in a migration - it is created by app/main.py's
Base.metadata.create_all() instead (see migration 009's docstring for the full
story on that split). Railway runs `alembic upgrade head` BEFORE uvicorn
imports app.main, so on a genuinely fresh database this table does not exist
yet at migration time. Both branches below are correct:
  - table exists (every current deployment): add the column.
  - table absent (fresh DB): skip - create_all() will create the table with
    this column already on it, since it is now part of the model.

Revision ID: 010_add_hypothesis_previous_strength
Revises: 009_add_state_trait_columns
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010_add_hypothesis_previous_strength'
down_revision: Union[str, Sequence[str], None] = '009_add_state_trait_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = 'clinical_pattern_hypotheses'
COLUMN = 'previous_evidence_strength'


def _table_columns(inspector):
    if TABLE not in inspector.get_table_names():
        return None
    return {c['name'] for c in inspector.get_columns(TABLE)}


def upgrade() -> None:
    """Upgrade schema."""
    columns = _table_columns(sa.inspect(op.get_bind()))
    if columns is None or COLUMN in columns:
        return
    with op.batch_alter_table(TABLE) as batch:
        batch.add_column(sa.Column(COLUMN, sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    columns = _table_columns(sa.inspect(op.get_bind()))
    if columns is None or COLUMN not in columns:
        return
    with op.batch_alter_table(TABLE) as batch:
        batch.drop_column(COLUMN)
