"""add feedback table

Revision ID: add_feedback_table
Revises: 007_add_persona_foundational_baseline
Create Date: 2024-12-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_feedback_table'
down_revision = '007_add_persona_foundational_baseline'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'feedback',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('page_context', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])


def downgrade():
    op.drop_index('ix_feedback_user_id', table_name='feedback')
    op.drop_table('feedback')
