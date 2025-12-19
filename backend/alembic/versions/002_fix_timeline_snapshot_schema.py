"""Fix TimelineSnapshot schema mismatch

Revision ID: fix_timeline_snapshot_schema
Revises: 87784065e333
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
down_revision = '87784065e333'  # Initial schema migration
branch_labels = None
depends_on = None


def upgrade():
    """
    Rename columns and add missing fields to match remix_service.py usage
    """
    # Check if timeline_snapshots table exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'timeline_snapshots' not in tables:
        # Table doesn't exist, create it with correct schema
        op.create_table(
            'timeline_snapshots',
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
        return
    
    # Table exists, need to modify it
    # Check if we're using SQLite or PostgreSQL
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
        # Check which old columns exist
        columns = [col['name'] for col in inspector.get_columns('timeline_snapshots')]
        
        # Build column mapping - use old names if they exist, otherwise use NULL
        personality_col = 'snapshot_personality' if 'snapshot_personality' in columns else 'NULL'
        symptoms_col = 'snapshot_symptoms' if 'snapshot_symptoms' in columns else 'NULL'
        severity_col = 'snapshot_symptom_severity' if 'snapshot_symptom_severity' in columns else 'NULL'
        
        op.execute(f"""
            INSERT INTO timeline_snapshots_new (
                id, persona_id, template_id, label, description, created_at,
                modified_experiences, modified_interventions,
                personality_snapshot, trauma_markers_snapshot, symptom_severity_snapshot,
                personality_difference, symptom_difference
            )
            SELECT 
                id, persona_id, template_id, label, description, created_at,
                modified_experiences, modified_interventions,
                {personality_col}, {symptoms_col}, {severity_col},
                NULL, NULL
            FROM timeline_snapshots
        """)
        
        # 3. Drop old table
        op.drop_table('timeline_snapshots')
        
        # 4. Rename new table
        op.rename_table('timeline_snapshots_new', 'timeline_snapshots')
        
    else:
        # PostgreSQL: Use ALTER TABLE
        
        # Rename existing columns (if they exist)
        columns = [col['name'] for col in inspector.get_columns('timeline_snapshots')]
        
        if 'snapshot_personality' in columns:
            op.alter_column('timeline_snapshots', 'snapshot_personality',
                           new_column_name='personality_snapshot')
        if 'snapshot_symptoms' in columns:
            op.alter_column('timeline_snapshots', 'snapshot_symptoms',
                           new_column_name='trauma_markers_snapshot')
        if 'snapshot_symptom_severity' in columns:
            op.alter_column('timeline_snapshots', 'snapshot_symptom_severity',
                           new_column_name='symptom_severity_snapshot')
        
        # Add new columns if they don't exist
        if 'personality_difference' not in columns:
            op.add_column('timeline_snapshots', 
                         sa.Column('personality_difference', sa.JSON(), nullable=True))
        if 'symptom_difference' not in columns:
            op.add_column('timeline_snapshots', 
                         sa.Column('symptom_difference', sa.JSON(), nullable=True))
        
        # Drop unused columns if they exist
        if 'snapshot_age' in columns:
            op.drop_column('timeline_snapshots', 'snapshot_age')
        if 'snapshot_attachment_style' in columns:
            op.drop_column('timeline_snapshots', 'snapshot_attachment_style')
        if 'snapshot_trauma_markers' in columns:
            op.drop_column('timeline_snapshots', 'snapshot_trauma_markers')


def downgrade():
    """
    Revert changes (rename back to old names)
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
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
        
        columns = [col['name'] for col in inspector.get_columns('timeline_snapshots')]
        
        if 'personality_difference' in columns:
            op.drop_column('timeline_snapshots', 'personality_difference')
        if 'symptom_difference' in columns:
            op.drop_column('timeline_snapshots', 'symptom_difference')
        
        if 'personality_snapshot' in columns:
            op.alter_column('timeline_snapshots', 'personality_snapshot',
                           new_column_name='snapshot_personality')
        if 'trauma_markers_snapshot' in columns:
            op.alter_column('timeline_snapshots', 'trauma_markers_snapshot',
                           new_column_name='snapshot_symptoms')
        if 'symptom_severity_snapshot' in columns:
            op.alter_column('timeline_snapshots', 'symptom_severity_snapshot',
                           new_column_name='snapshot_symptom_severity')
        
        if 'snapshot_age' not in columns:
            op.add_column('timeline_snapshots',
                         sa.Column('snapshot_age', sa.JSON(), nullable=False))

