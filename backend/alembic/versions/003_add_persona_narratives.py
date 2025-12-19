"""Add persona_narratives table

Revision ID: add_persona_narratives
Revises: (update this to your latest migration)
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_persona_narratives'
down_revision = 'fix_timeline_snapshot_schema'  # Update this!
branch_labels = None
depends_on = None


def upgrade():
    """
    Create persona_narratives table for storing AI-generated narratives.
    """
    op.create_table(
        'persona_narratives',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('persona_id', sa.String(), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('generation_number', sa.Integer(), nullable=False),
        sa.Column('persona_age_at_generation', sa.Integer(), nullable=False),
        sa.Column('total_experiences_count', sa.Integer(), nullable=False),
        sa.Column('total_interventions_count', sa.Integer(), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('developmental_timeline', sa.Text(), nullable=False),
        sa.Column('current_presentation', sa.Text(), nullable=False),
        sa.Column('treatment_response', sa.Text(), nullable=True),
        sa.Column('prognosis', sa.Text(), nullable=False),
        sa.Column('full_narrative', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('generation_time_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add index on persona_id for faster lookups
    op.create_index(
        'ix_persona_narratives_persona_id',
        'persona_narratives',
        ['persona_id']
    )


def downgrade():
    """
    Remove persona_narratives table.
    """
    op.drop_index('ix_persona_narratives_persona_id', table_name='persona_narratives')
    op.drop_table('persona_narratives')
