"""Rules about reservations that more than one team's code needs.

    student pays the security deposit in JSM's Entrata
        │  the sync job copies it into the deposits table (app/entrata/sync.py)
        ▼
    student clicks Reserve, with the same email ──▶ confirmed ──staff cancels──▶ cancelled
                                                    unit leaves the list           unit is back on the list,
                                                                                   deposit can reserve again

No holds. A unit stays on the list until a student who has already paid reserves it,
so nobody can tie up a unit they haven't paid for.
"""

from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Deposit, Reservation


def utcnow() -> datetime:
    return datetime.now(UTC)


def unused_deposits() -> Select[tuple[Deposit]]:
    """Deposits that can still reserve a unit: not refunded, and not already
    paying for a confirmed reservation."""
    in_use = select(Reservation.id).where(
        Reservation.deposit_id == Deposit.id, Reservation.status == "confirmed"
    )
    return select(Deposit).where(Deposit.refunded_at.is_(None), ~in_use.exists())


def unused_deposit_for(db: Session, email: str, lock: bool = False) -> Deposit | None:
    """This student's oldest unused deposit, or None if they haven't paid one (yet).

    lock=True holds the row until the transaction ends, so staff can't mark it
    refunded in the middle of the student reserving with it.
    """
    query = (
        unused_deposits()
        .where(Deposit.payer_email == email)
        .order_by(Deposit.paid_at, Deposit.id)
        .limit(1)
    )
    if lock:
        query = query.with_for_update(of=Deposit)
    return db.scalar(query)


def confirmed_reservation_for(db: Session, email: str) -> Reservation | None:
    """The unit this student has reserved, if any (their most recent)."""
    return db.scalar(
        select(Reservation)
        .where(Reservation.student_email == email, Reservation.status == "confirmed")
        .order_by(Reservation.created_at.desc(), Reservation.id.desc())
        .limit(1)
    )


def violated_constraint(error: IntegrityError) -> str | None:
    """Which database rule an insert or update broke, e.g. "one_active_reservation_per_apartment"."""
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def unit_name(reservation: Reservation) -> str:
    return f"{reservation.apartment.building} {reservation.apartment.number}"
