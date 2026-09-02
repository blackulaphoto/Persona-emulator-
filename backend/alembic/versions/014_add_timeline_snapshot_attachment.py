"""Capture attachment in timeline snapshots.

State was wired into TimelineSnapshot at Step 11f (state_profile_snapshot,
added for real in migration 009); attachment never was, even though it's
tracked live on Persona the same way. Compare could diff Big Five and State
between two points in a life but never attachment. This is a real ALTER on
an existing table (timeline_snapshots predates this migration and already
has rows in local dev), so it needs a real migration rather than relying on
Base.metadata.create_all().

Scoped to only these two genuinely new columns - state_profile_snapshot is
already owned by migration 009 and is not touched here.

Revision ID: 014_add_snapshot_attachment
Revises: 013_add_sequence_index
"""
from alembic import op
import sqlalchemy as sa

# Shortened from '014_add_timeline_snapshot_attachment' (36 chars) - see
# 007's revision comment for why (alembic_version.version_num is
# VARCHAR(32) in Postgres).
revision = "014_add_snapshot_attachment"
down_revision = "013_add_sequence_index"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {col["name"] for col in inspector.get_columns("timeline_snapshots")}

    if "attachment_style_snapshot" not in existing_columns:
        op.add_column("timeline_snapshots", sa.Column("attachment_style_snapshot", sa.String(), nullable=True))
    if "attachment_dimensions_snapshot" not in existing_columns:
        op.add_column("timeline_snapshots", sa.Column("attachment_dimensions_snapshot", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("timeline_snapshots", "attachment_dimensions_snapshot")
    op.drop_column("timeline_snapshots", "attachment_style_snapshot")
