"""Fills an empty database with the same sample data for everyone.

Runs automatically when the api container starts, and only when the apartments
table is empty, so it never overwrites your changes.
To wipe your database and start over: docker compose down -v, then docker compose up
"""

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Apartment, Deposit, Reservation

# The four units from the kickoff mock (slide 2)
AVAILABLE_APARTMENTS = [
    dict(number="A-101", building="Building A", bedrooms=1, price_cents=72_500),
    dict(number="A-204", building="Building A", bedrooms=2, price_cents=85_000),
    dict(number="B-110", building="Building B", bedrooms=2, price_cents=89_000),
    dict(number="C-302", building="Building C", bedrooms=3, price_cents=114_000),
]

# Has paid a deposit and hasn't reserved yet, so Reserve works for this email right away
PAID_STUDENT_EMAIL = "paid.student@example.com"


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Apartment)):
            print("Seed: the database already has apartments, skipping.")
            return

        db.add_all([Apartment(**fields) for fields in AVAILABLE_APARTMENTS])

        # A fifth unit that's already taken, so lists have something to filter out
        # and the staff page has a reservation to show.
        taken = Apartment(
            number="B-215", building="Building B", bedrooms=1, price_cents=76_000, available=False
        )
        db.add(taken)
        db.add(
            Reservation(
                apartment=taken,
                student_name="Test Student",
                student_email="test.student@example.com",
                status="confirmed",
                deposit=Deposit(
                    entrata_id="SEED-DEPOSIT-1",
                    payer_email="test.student@example.com",
                    amount_cents=50_000,
                    paid_at=func.now(),
                ),
                entrata_unit_marked=True,
            )
        )
        db.add(
            Deposit(
                entrata_id="SEED-DEPOSIT-2",
                payer_email=PAID_STUDENT_EMAIL,
                amount_cents=50_000,
                paid_at=func.now(),
            )
        )
        db.commit()
        print(
            "Seed: added 5 apartments (4 available), 1 reservation, and a paid deposit "
            f"for {PAID_STUDENT_EMAIL} so you can try Reserve."
        )


if __name__ == "__main__":
    seed()
