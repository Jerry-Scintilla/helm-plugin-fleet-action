"""initial fleet_action tables

Revision ID: 0001fleet_action
Revises:
Create Date: 2026-04-28

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

revision = "0001fleet_action"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE fleet_action_status AS ENUM ('active', 'ended'); "
        "EXCEPTION WHEN duplicate_object THEN null; "
        "END $$;"
    ))

    op.create_table(
        "fleet_action_actions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("fleet_id", sa.BigInteger(), nullable=False),
        sa.Column("fc_character_id", sa.BigInteger(), nullable=False),
        sa.Column("fc_character_name", sa.String(256), nullable=False),
        sa.Column(
            "status",
            PgEnum("active", "ended", name="fleet_action_status", create_type=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        if_not_exists=True,
    )
    op.create_index("ix_fleet_action_actions_fleet_id", "fleet_action_actions", ["fleet_id"],
                    if_not_exists=True)
    op.create_index("ix_fleet_action_actions_fc_character_id", "fleet_action_actions", ["fc_character_id"],
                    if_not_exists=True)
    op.create_index("ix_fleet_action_actions_status", "fleet_action_actions", ["status"],
                    if_not_exists=True)

    op.create_table(
        "fleet_action_pap_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "action_id",
            sa.Integer(),
            sa.ForeignKey("fleet_action_actions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("character_id", sa.BigInteger(), nullable=False),
        sa.Column("character_name", sa.String(256), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_by_character_id", sa.BigInteger(), nullable=False),
        if_not_exists=True,
    )
    op.create_index("ix_fleet_action_pap_records_action_id", "fleet_action_pap_records", ["action_id"],
                    if_not_exists=True)


def downgrade() -> None:
    op.drop_table("fleet_action_pap_records")
    op.drop_table("fleet_action_actions")
    # Same reasoning as upgrade — use raw SQL to stay inside the transaction
    op.execute(sa.text("DROP TYPE IF EXISTS fleet_action_status"))
