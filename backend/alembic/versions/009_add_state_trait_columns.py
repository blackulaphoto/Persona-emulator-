"""add State/Trait split columns and narrative_mode (Steps 9/11a/11e/11f)

Backfills every model column added since the last migration (008) that was
never captured in an Alembic migration - relying instead on
app/main.py's Base.metadata.create_all(bind=engine), which creates brand-new
tables on deploy but never alters columns onto tables that already exist in
production. Confirmed empirically: a fresh SQLite DB built ONLY from
alembic upgrade head is missing all of these columns compared to the full
current ORM schema, while production (create-persona) started 500ing after
Step 11 shipped - narrative_mode predates Step 11 entirely, so this gap was
silently present before this rebuild too, just never hit until current_state
also went missing on the very same table.

Revision ID: 009_add_state_trait_columns
Revises: add_persona_symptoms_tables
Create Date: 2026-08-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_add_state_trait_columns'
down_revision: Union[str, Sequence[str], None] = 'add_persona_symptoms_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('personas') as batch:
        # Predates Step 11 (Evidence & Source Model) - narrative attribution
        # mode, defaults to "case_subject" for every existing row.
        batch.add_column(
            sa.Column('narrative_mode', sa.String(), nullable=False, server_default=sa.text("'case_subject'"))
        )
        # Step 11a: the fast-moving State tier - starts empty for every
        # existing row, same "unearned defaults are what this rebuild
        # removed elsewhere" reasoning as current_trauma_markers.
        batch.add_column(
            sa.Column('current_state', sa.JSON(), nullable=False, server_default=sa.text("'{}'"))
        )

    with op.batch_alter_table('personality_snapshots') as batch:
        # Step 11a: frozen State-tier copy, parallel to personality_profile.
        batch.add_column(sa.Column('state_profile', sa.JSON(), nullable=True))

    with op.batch_alter_table('interventions') as batch:
        # Step 11e: which AdaptationPattern this intervention targeted, and
        # the State/Trait proposal actually produced for it.
        batch.add_column(sa.Column('targeted_adaptation_strategy', sa.String(length=50), nullable=True))
        batch.add_column(sa.Column('state_implications', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('trait_implications', sa.JSON(), nullable=True))

    with op.batch_alter_table('timeline_snapshots') as batch:
        # Step 9: frozen pattern/hypothesis snapshots - predates Step 11,
        # same never-migrated gap.
        batch.add_column(sa.Column('adaptation_patterns_snapshot', sa.JSON(), nullable=True))
        batch.add_column(sa.Column('clinical_pattern_hypotheses_snapshot', sa.JSON(), nullable=True))
        # Step 11f: frozen State-tier copy for remix/timeline comparisons.
        batch.add_column(sa.Column('state_profile_snapshot', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('timeline_snapshots') as batch:
        batch.drop_column('state_profile_snapshot')
        batch.drop_column('clinical_pattern_hypotheses_snapshot')
        batch.drop_column('adaptation_patterns_snapshot')

    with op.batch_alter_table('interventions') as batch:
        batch.drop_column('trait_implications')
        batch.drop_column('state_implications')
        batch.drop_column('targeted_adaptation_strategy')

    with op.batch_alter_table('personality_snapshots') as batch:
        batch.drop_column('state_profile')

    with op.batch_alter_table('personas') as batch:
        batch.drop_column('current_state')
        batch.drop_column('narrative_mode')
