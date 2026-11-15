"""Allow apartment rents to be displayed as ranges from the rate sheet."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("apartments", sa.Column("price_max_cents", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("apartments", "price_max_cents")
