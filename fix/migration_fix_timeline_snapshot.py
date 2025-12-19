"""Fix TimelineSnapshot schema mismatch

Revision ID: fix_timeline_snapshot_schema
Revises: add_clinical_templates
Create Date: 2025-12-17

This migration:
1. Renames columns to match service usage
2. Adds missing columns (personality_difference, symptom_difference)
3. Removes snapshot_age column (not used)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_timeline_snapshot_schema'
down_revision = 'add_clinical_templates'  # Update this to your actual previous migration ID
branch_labels = None
depends_on = None


def upgrade():
    """
    Rename columns and add missing fields to match remix_service.py usage
    """
    # For SQLite, we need to recreate the table (no ALTER COLUMN support)
    # For PostgreSQL, we can use ALTER TABLE directly
    
    # Check if we're using SQLite or PostgreSQL
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'sqlite':
        # SQLite: Create new table, copy data, drop old table, rename new
        
        # 1. Create new table with correct schema
        op.create_table(
            'timeline_snapshots_new',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('persona_id', sa.String(), nullable=False),
            sa.Column('template_id', sa.String(), nullable=True),
            sa.Column('label', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('modified_experiences', sa.JSON(), nullable=False),
            sa.Column('modified_interventions', sa.JSON(), nullable=True),
            # CORRECTED NAMES:
            sa.Column('personality_snapshot', sa.JSON(), nullable=False),
            sa.Column('trauma_markers_snapshot', sa.JSON(), nullable=True),
            sa.Column('symptom_severity_snapshot', sa.JSON(), nullable=True),
            # NEW COLUMNS:
            sa.Column('personality_difference', sa.JSON(), nullable=True),
            sa.Column('symptom_difference', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # 2. Copy data with column name mapping
        op.execute("""
            INSERT INTO timeline_snapshots_new (
                id, persona_id, template_id, label, description, created_at,
                modified_experiences, modified_interventions,
                personality_snapshot, trauma_markers_snapshot, symptom_severity_snapshot,
                personality_difference, symptom_difference
            )
            SELECT 
                id, persona_id, template_id, label, description, created_at,
                modified_experiences, modified_interventions,
                snapshot_personality, snapshot_symptoms, snapshot_symptom_severity,
                NULL, NULL
            FROM timeline_snapshots
        """)
        
        # 3. Drop old table
        op.drop_table('timeline_snapshots')
        
        # 4. Rename new table
        op.rename_table('timeline_snapshots_new', 'timeline_snapshots')
        
    else:
        # PostgreSQL: Use ALTER TABLE
        
        # Rename existing columns
        op.alter_column('timeline_snapshots', 'snapshot_personality',
                       new_column_name='personality_snapshot')
        op.alter_column('timeline_snapshots', 'snapshot_symptoms',
                       new_column_name='trauma_markers_snapshot')
        op.alter_column('timeline_snapshots', 'snapshot_symptom_severity',
                       new_column_name='symptom_severity_snapshot')
        
        # Add new columns
        op.add_column('timeline_snapshots', 
                     sa.Column('personality_difference', sa.JSON(), nullable=True))
        op.add_column('timeline_snapshots', 
                     sa.Column('symptom_difference', sa.JSON(), nullable=True))
        
        # Drop unused column if it exists
        try:
            op.drop_column('timeline_snapshots', 'snapshot_age')
        except:
            pass  # Column may not exist


def downgrade():
    """
    Revert changes (rename back to old names)
    """
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    if dialect == 'sqlite':
        # SQLite: Create old table, copy data, drop new table, rename
        
        op.create_table(
            'timeline_snapshots_old',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('persona_id', sa.String(), nullable=False),
            sa.Column('template_id', sa.String(), nullable=True),
            sa.Column('label', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('modified_experiences', sa.JSON(), nullable=False),
            sa.Column('modified_interventions', sa.JSON(), nullable=True),
            # OLD NAMES:
            sa.Column('snapshot_personality', sa.JSON(), nullable=False),
            sa.Column('snapshot_symptoms', sa.JSON(), nullable=False),
            sa.Column('snapshot_symptom_severity', sa.JSON(), nullable=False),
            sa.Column('snapshot_age', sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(['persona_id'], ['personas.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        op.execute("""
            INSERT INTO timeline_snapshots_old (
                id, persona_id, template_id, label, description, created_at,
                modified_experiences, modified_interventions,
                snapshot_personality, snapshot_symptoms, snapshot_symptom_severity,
                snapshot_age
            )
            SELECT 
                id, persona_id, template_id, label, description, created_at,
                modified_experiences, modified_interventions,
                personality_snapshot, trauma_markers_snapshot, symptom_severity_snapshot,
                '{}'
            FROM timeline_snapshots
        """)
        
        op.drop_table('timeline_snapshots')
        op.rename_table('timeline_snapshots_old', 'timeline_snapshots')
        
    else:
        # PostgreSQL: Rename back
        
        op.drop_column('timeline_snapshots', 'personality_difference')
        op.drop_column('timeline_snapshots', 'symptom_difference')
        
        op.alter_column('timeline_snapshots', 'personality_snapshot',
                       new_column_name='snapshot_personality')
        op.alter_column('timeline_snapshots', 'trauma_markers_snapshot',
                       new_column_name='snapshot_symptoms')
        op.alter_column('timeline_snapshots', 'symptom_severity_snapshot',
                       new_column_name='snapshot_symptom_severity')
        
        op.add_column('timeline_snapshots',
                     sa.Column('snapshot_age', sa.JSON(), nullable=False))
