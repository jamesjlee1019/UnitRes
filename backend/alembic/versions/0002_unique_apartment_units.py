"""A building can't have the same unit number twice.

Before this, the staff form could add "D-410 in Building D" more than once,
and the apartments page would list it twice.

Revision ID: 0002
Revises: 59ed6f66772a (the accounts table)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "59ed6f66772a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # If you added the same unit twice while testing the staff form, the database
    # can't add this rule yet. Stop with a message that says how to fix it.
    duplicates = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT building, number FROM apartments "
                "GROUP BY building, number HAVING count(*) > 1"
            )
        )
        .all()
    )
    if duplicates:
        units = ", ".join(f"{number} in {building}" for building, number in duplicates)
        raise RuntimeError(
            f"Your database has these units more than once: {units}. "
            "To start over with the sample data, run: docker compose down -v, "
            "then docker compose up"
        )

    op.create_unique_constraint(
        "apartment_unit_is_unique", "apartments", ["building", "number"]
    )


def downgrade() -> None:
    op.drop_constraint("apartment_unit_is_unique", "apartments", type_="unique")
