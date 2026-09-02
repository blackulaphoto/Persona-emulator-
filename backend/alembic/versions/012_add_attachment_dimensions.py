"""Add developmental attachment dimensions.

Revision ID: 012_add_attachment_dimensions
Revises: 011_add_baseline_personality
"""
from alembic import op
import sqlalchemy as sa

revision = "012_add_attachment_dimensions"
down_revision = "011_add_baseline_personality"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("personas", sa.Column("baseline_attachment_style", sa.String(), nullable=True))
    op.add_column("personas", sa.Column("baseline_attachment_dimensions", sa.JSON(), nullable=True))
    op.add_column("personas", sa.Column("current_attachment_dimensions", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("personality_snapshots", sa.Column("attachment_dimensions", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("personality_snapshots", "attachment_dimensions")
    op.drop_column("personas", "current_attachment_dimensions")
    op.drop_column("personas", "baseline_attachment_dimensions")
    op.drop_column("personas", "baseline_attachment_style")
