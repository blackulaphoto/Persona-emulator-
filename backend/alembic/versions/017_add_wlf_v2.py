"""Add Whole-Life Formulation V2 persistence tables + Persona.formulation_engine_version.

Additive only - no existing table touched or dropped. Two new tables
(whole_life_formulations, formulation_validation_reports) plus one new
column on personas. Both new tables FK to personas.id with ON DELETE CASCADE
from the start (unlike the legacy tables that needed migration 015/016 to
retrofit this) - personas.id is a real, always-populated primary key, so
there's no analog of the vestigial fk_personas_user_id problem here.

Revision ID: 017_add_wlf_v2
Revises: 016_add_snapshot_fk_cascade
"""
from alembic import op
import sqlalchemy as sa

revision = "017_add_wlf_v2"
down_revision = "016_add_snapshot_fk_cascade"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("personas") as batch:
        batch.add_column(
            sa.Column(
                "formulation_engine_version",
                sa.String(length=10),
                nullable=False,
                server_default="v1",
            )
        )

    op.create_table(
        "whole_life_formulations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("persona_id", sa.String(), nullable=False),
        sa.Column("engine_version", sa.String(length=30), nullable=False),
        sa.Column("schema_version", sa.String(length=30), nullable=False),
        sa.Column("generation_number", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("model_id", sa.String(length=100), nullable=False),
        sa.Column("formulation_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["persona_id"], ["personas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_whole_life_formulations_persona_id", "whole_life_formulations", ["persona_id"]
    )

    op.create_table(
        "formulation_validation_reports",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("formulation_id", sa.String(), nullable=True),
        sa.Column("attempted_generation_id", sa.String(length=64), nullable=False),
        sa.Column("persona_id", sa.String(), nullable=False),
        sa.Column("claim_type", sa.String(length=30), nullable=False),
        sa.Column("claim_ref", sa.String(length=150), nullable=False),
        sa.Column("rule_violated", sa.String(length=50), nullable=False),
        sa.Column("action_taken", sa.String(length=30), nullable=False),
        sa.Column("rejection_reason", sa.String(), nullable=False),
        sa.Column("raw_claim_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["formulation_id"], ["whole_life_formulations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["persona_id"], ["personas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_formulation_validation_reports_formulation_id",
        "formulation_validation_reports", ["formulation_id"],
    )
    op.create_index(
        "ix_formulation_validation_reports_attempted_generation_id",
        "formulation_validation_reports", ["attempted_generation_id"],
    )
    op.create_index(
        "ix_formulation_validation_reports_persona_id",
        "formulation_validation_reports", ["persona_id"],
    )


def downgrade():
    op.drop_index(
        "ix_formulation_validation_reports_persona_id", table_name="formulation_validation_reports"
    )
    op.drop_index(
        "ix_formulation_validation_reports_attempted_generation_id",
        table_name="formulation_validation_reports",
    )
    op.drop_index(
        "ix_formulation_validation_reports_formulation_id", table_name="formulation_validation_reports"
    )
    op.drop_table("formulation_validation_reports")
    op.drop_index("ix_whole_life_formulations_persona_id", table_name="whole_life_formulations")
    op.drop_table("whole_life_formulations")
    with op.batch_alter_table("personas") as batch:
        batch.drop_column("formulation_engine_version")
