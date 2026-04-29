"""make fleet_action_actions.fleet_id nullable

Revision ID: 0002fleet_action
Revises: 0001fleet_action
Create Date: 2026-04-29

"""

import sqlalchemy as sa
from alembic import op

revision = "0002fleet_action"
down_revision = "0001fleet_action"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("fleet_action_actions", "fleet_id", nullable=True)


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE fleet_action_actions SET fleet_id = 0 WHERE fleet_id IS NULL"
    ))
    op.alter_column("fleet_action_actions", "fleet_id", nullable=False)
