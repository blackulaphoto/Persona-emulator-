"""Persist immutable persona baseline personality.

Revision ID: 011_add_persona_baseline_personality
Revises: 010_add_hypothesis_previous_strength
"""
from alembic import op
import sqlalchemy as sa


revision = "011_add_persona_baseline_personality"
down_revision = "010_add_hypothesis_previous_strength"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("personas", sa.Column("baseline_personality", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("personas", "baseline_personality")
