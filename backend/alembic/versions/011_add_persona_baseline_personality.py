"""Persist immutable persona baseline personality.

Revision ID: 011_add_baseline_personality
Revises: 010_add_hypothesis_prev_str
"""
from alembic import op
import sqlalchemy as sa


# Shortened from '011_add_persona_baseline_personality' (36 chars) - see
# 007's revision comment for why (alembic_version.version_num is
# VARCHAR(32) in Postgres).
revision = "011_add_baseline_personality"
down_revision = "010_add_hypothesis_prev_str"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("personas", sa.Column("baseline_personality", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("personas", "baseline_personality")
