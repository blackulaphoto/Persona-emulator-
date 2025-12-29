"""Add persona_symptoms and symptom_history tables

Revision ID: add_persona_symptoms_tables
Revises: 007_add_persona_foundational_baseline
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_persona_symptoms_tables'
down_revision = '007_add_persona_foundational_baseline'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create persona_symptoms and symptom_history tables for comprehensive DSM-5/ICD-11 symptom tracking.
    """

    # Create persona_symptoms table
    op.create_table(
        'persona_symptoms',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('persona_id', sa.String(), nullable=False),
        sa.Column('symptom_name', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('first_onset_age', sa.Integer(), nullable=True),
        sa.Column('current_status', sa.String(length=50), nullable=True),
        sa.Column('symptom_details', sa.JSON(), nullable=True),
        sa.Column('contributing_experience_ids', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add index on persona_id for faster lookups
    op.create_index(
        'ix_persona_symptoms_persona_id',
        'persona_symptoms',
        ['persona_id']
    )

    # Create symptom_history table
    op.create_table(
        'symptom_history',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('persona_id', sa.String(), nullable=False),
        sa.Column('symptom_id', sa.String(), nullable=False),
        sa.Column('symptom_name', sa.String(length=100), nullable=False),
        sa.Column('severity_before', sa.Float(), nullable=True),
        sa.Column('severity_after', sa.Float(), nullable=True),
        sa.Column('age_at_change', sa.Integer(), nullable=True),
        sa.Column('trigger_type', sa.String(length=50), nullable=True),
        sa.Column('trigger_id', sa.String(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
        sa.ForeignKeyConstraint(['symptom_id'], ['persona_symptoms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add indexes for faster lookups
    op.create_index(
        'ix_symptom_history_persona_id',
        'symptom_history',
        ['persona_id']
    )

    op.create_index(
        'ix_symptom_history_symptom_id',
        'symptom_history',
        ['symptom_id']
    )


def downgrade():
    """
    Remove persona_symptoms and symptom_history tables.
    """
    op.drop_index('ix_symptom_history_symptom_id', table_name='symptom_history')
    op.drop_index('ix_symptom_history_persona_id', table_name='symptom_history')
    op.drop_table('symptom_history')

    op.drop_index('ix_persona_symptoms_persona_id', table_name='persona_symptoms')
    op.drop_table('persona_symptoms')
