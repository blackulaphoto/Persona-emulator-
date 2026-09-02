"""Cascade-delete personality_snapshots when their experience/intervention is deleted.

Genuine Postgres compatibility bug, found live: deleting a persona failed with
ForeignKeyViolation ("update or delete on table experiences violates foreign
key constraint personality_snapshots_experience_id_fkey ... still referenced
from table personality_snapshots") whenever that persona had any personality
snapshots. Root cause: Persona.experiences and Persona.snapshots are two
independent cascade="all, delete-orphan" relationships on Persona, and there
is no ORM relationship() connecting Experience/Intervention to
PersonalitySnapshot - so SQLAlchemy's unit-of-work has no way to order a
delete-persona flush so snapshot rows are removed before the experience/
intervention rows they reference. SQLite doesn't enforce foreign keys by
default, so this was silently never a problem there; Postgres enforces them
strictly and rejected every persona delete once Postgres was actually
connected and the persona had snapshots.

Adding ON DELETE CASCADE on both FKs removes the ordering dependency
entirely - Postgres cascades the snapshot deletion itself as part of
deleting the referenced experience/intervention row, regardless of what
order the ORM issues its DELETE statements in.

Revision ID: 016_add_snapshot_fk_cascade
Revises: 015_drop_personas_user_fk
"""
from alembic import op

revision = "016_add_snapshot_fk_cascade"
down_revision = "015_drop_personas_user_fk"
branch_labels = None
depends_on = None

# The original migration (87784065e333) created these two FKs unnamed, so
# Postgres auto-derived '<table>_<column>_fkey' names for them; SQLite does
# not reflect the same names for an unnamed constraint, and doesn't enforce
# FKs by default in the first place (so there is nothing to fix there - this
# is a genuine Postgres-only compatibility gap, not a portable schema change).
# Restricting this migration to postgresql avoids guessing at a SQLite
# constraint name that doesn't reliably exist.


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    with op.batch_alter_table("personality_snapshots") as batch:
        batch.drop_constraint(
            "personality_snapshots_experience_id_fkey", type_="foreignkey"
        )
        batch.create_foreign_key(
            "personality_snapshots_experience_id_fkey",
            "experiences",
            ["experience_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch.drop_constraint(
            "personality_snapshots_intervention_id_fkey", type_="foreignkey"
        )
        batch.create_foreign_key(
            "personality_snapshots_intervention_id_fkey",
            "interventions",
            ["intervention_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    with op.batch_alter_table("personality_snapshots") as batch:
        batch.drop_constraint(
            "personality_snapshots_experience_id_fkey", type_="foreignkey"
        )
        batch.create_foreign_key(
            "personality_snapshots_experience_id_fkey",
            "experiences",
            ["experience_id"],
            ["id"],
        )
        batch.drop_constraint(
            "personality_snapshots_intervention_id_fkey", type_="foreignkey"
        )
        batch.create_foreign_key(
            "personality_snapshots_intervention_id_fkey",
            "interventions",
            ["intervention_id"],
            ["id"],
        )
