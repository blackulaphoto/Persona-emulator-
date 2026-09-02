"""Add stable same-age experience ordering.

Revision ID: 013_add_sequence_index
Revises: 012_add_attachment_dimensions
"""
from alembic import op
import sqlalchemy as sa

# Shortened from '013_add_experience_sequence_index' (33 chars) - see 007's
# revision comment for why (alembic_version.version_num is VARCHAR(32) in
# Postgres).
revision = "013_add_sequence_index"
down_revision = "012_add_attachment_dimensions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "experiences",
        sa.Column("sequence_index", sa.Integer(), nullable=False, server_default="1"),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, persona_id, age_at_event FROM experiences "
            "ORDER BY persona_id, age_at_event, sequence_number, created_at, id"
        )
    ).fetchall()
    next_index = {}
    for row in rows:
        key = (row.persona_id, row.age_at_event)
        next_index[key] = next_index.get(key, 0) + 1
        connection.execute(
            sa.text("UPDATE experiences SET sequence_index = :value WHERE id = :id"),
            {"value": next_index[key], "id": row.id},
        )


def downgrade():
    op.drop_column("experiences", "sequence_index")
