"""Add user_id to all tables

Revision ID: add_user_id_columns
Revises: add_persona_narratives
Create Date: 2025-12-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_id_columns'
down_revision = 'add_persona_narratives'  # Update to your latest migration!
branch_labels = None
depends_on = None


def upgrade():
    """
    Add user_id column to all user-scoped tables.
    """
    # Add user_id to personas table
    op.add_column('personas', sa.Column('user_id', sa.String(), nullable=True))
    op.create_index('ix_personas_user_id', 'personas', ['user_id'])
    
    # Add user_id to experiences table
    op.add_column('experiences', sa.Column('user_id', sa.String(), nullable=True))
    op.create_index('ix_experiences_user_id', 'experiences', ['user_id'])
    
    # Add user_id to interventions table
    op.add_column('interventions', sa.Column('user_id', sa.String(), nullable=True))
    op.create_index('ix_interventions_user_id', 'interventions', ['user_id'])
    
    # Add user_id to persona_narratives table
    op.add_column('persona_narratives', sa.Column('user_id', sa.String(), nullable=True))
    op.create_index('ix_persona_narratives_user_id', 'persona_narratives', ['user_id'])
    
    # Note: For existing data, you may want to assign a default user_id
    # Or delete test data before running this migration


def downgrade():
    """
    Remove user_id columns.
    """
    op.drop_index('ix_persona_narratives_user_id', table_name='persona_narratives')
    op.drop_column('persona_narratives', 'user_id')
    
    op.drop_index('ix_interventions_user_id', table_name='interventions')
    op.drop_column('interventions', 'user_id')
    
    op.drop_index('ix_experiences_user_id', table_name='experiences')
    op.drop_column('experiences', 'user_id')
    
    op.drop_index('ix_personas_user_id', table_name='personas')
    op.drop_column('personas', 'user_id')
