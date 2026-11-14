"""Entrata handoff: pay the deposit in Entrata first, then reserve. No holds.

- New deposits table: every security deposit seen in JSM's Entrata.
- A reservation is now "confirmed" (paid for by a deposit) or "cancelled".
  "held" and "expired" are gone, along with expires_at.
- reservations.paid goes away. A confirmed reservation always has a deposit_id,
  so keeping both would give two answers that could disagree.
- Unique indexes: one confirmed reservation per apartment, and per deposit.

Older reservations: held and expired ones become cancelled. Confirmed ones get a
placeholder deposit ("BEFORE-ENTRATA-<id>", $0) so they keep their unit.

If a unique index fails to build, your local database has two confirmed reservations
for the same apartment. Run "docker compose down -v" and "docker compose up" to reset it.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deposits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entrata_id", sa.String(length=100), nullable=False),
        sa.Column("payer_email", sa.String(length=320), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entrata_id"),
    )
    op.create_index("ix_deposits_payer_email", "deposits", ["payer_email"])

    op.add_column("reservations", sa.Column("deposit_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "reservations_deposit_id_fkey", "reservations", "deposits", ["deposit_id"], ["id"]
    )
    op.add_column(
        "reservations",
        sa.Column(
            "entrata_unit_marked", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )

    # Carry existing data over
    op.execute("UPDATE reservations SET student_email = lower(trim(student_email))")
    op.execute(
        """
        INSERT INTO deposits (entrata_id, payer_email, amount_cents, paid_at)
        SELECT 'BEFORE-ENTRATA-' || id, student_email, 0, created_at
        FROM reservations WHERE status = 'confirmed'
        """
    )
    op.execute(
        """
        UPDATE reservations r SET deposit_id = d.id
        FROM deposits d WHERE d.entrata_id = 'BEFORE-ENTRATA-' || r.id
        """
    )
    op.execute("UPDATE reservations SET status = 'cancelled' WHERE status IN ('held', 'expired')")

    op.drop_column("reservations", "paid")
    op.drop_column("reservations", "expires_at")
    op.drop_constraint("reservation_status_is_valid", "reservations", type_="check")
    op.create_check_constraint(
        "reservation_status_is_valid", "reservations", "status IN ('confirmed', 'cancelled')"
    )
    op.alter_column("reservations", "status", server_default="confirmed")
    op.create_check_constraint(
        "confirmed_reservation_has_deposit",
        "reservations",
        "status = 'cancelled' OR deposit_id IS NOT NULL",
    )

    op.create_index(
        "one_active_reservation_per_apartment",
        "reservations",
        ["apartment_id"],
        unique=True,
        postgresql_where=sa.text("status = 'confirmed'"),
    )
    op.create_index(
        "one_active_reservation_per_deposit",
        "reservations",
        ["deposit_id"],
        unique=True,
        postgresql_where=sa.text("status = 'confirmed'"),
    )


def downgrade() -> None:
    op.drop_index("one_active_reservation_per_deposit", table_name="reservations")
    op.drop_index("one_active_reservation_per_apartment", table_name="reservations")
    op.drop_constraint("confirmed_reservation_has_deposit", "reservations", type_="check")
    op.drop_constraint("reservation_status_is_valid", "reservations", type_="check")
    op.create_check_constraint(
        "reservation_status_is_valid",
        "reservations",
        "status IN ('held', 'confirmed', 'expired', 'cancelled')",
    )
    op.alter_column("reservations", "status", server_default="held")

    op.add_column("reservations", sa.Column("expires_at", sa.DateTime(timezone=True)))
    op.add_column(
        "reservations",
        sa.Column("paid", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.execute("UPDATE reservations SET paid = (status = 'confirmed')")

    op.drop_column("reservations", "entrata_unit_marked")
    op.drop_constraint("reservations_deposit_id_fkey", "reservations", type_="foreignkey")
    op.drop_column("reservations", "deposit_id")
    op.drop_index("ix_deposits_payer_email", table_name="deposits")
    op.drop_table("deposits")
