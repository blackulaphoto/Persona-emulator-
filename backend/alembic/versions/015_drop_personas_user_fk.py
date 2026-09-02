"""Drop personas.user_id's foreign key to the unused users table.

Genuine Postgres compatibility bug, found live: personas.user_id stores a
Firebase UID (see app/core/auth.py - every real user is a verified Firebase
UID, nothing in this app ever writes a row to the `users` table). The
fk_personas_user_id constraint (added in 6e28795dc8ca) required that UID to
already exist as a row in `users`, which is never true. SQLite doesn't
enforce foreign keys by default, so this was silently never a problem
there; Postgres enforces them strictly, and rejected every real persona
create with ForeignKeyViolation once Postgres was actually connected.

Revision ID: 015_drop_personas_user_fk
Revises: 014_add_snapshot_attachment
"""
from alembic import op

revision = "015_drop_personas_user_fk"
down_revision = "014_add_snapshot_attachment"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("personas") as batch:
        batch.drop_constraint("fk_personas_user_id", type_="foreignkey")


def downgrade():
    with op.batch_alter_table("personas") as batch:
        batch.create_foreign_key(
            "fk_personas_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
