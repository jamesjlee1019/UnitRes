"""PAYMENTS TEAM: security deposits, paid through JSM's Entrata.

UnitRes doesn't take payments. Students apply and pay the security deposit in JSM's
Entrata, and the sync job in app/entrata/sync.py copies each deposit into the deposits
table. A deposit is what lets a student reserve (see app/routers/booking.py).

These are the staff side of that:

POST /admin/entrata/sync               check Entrata for new deposits now, instead of waiting
GET  /admin/deposits                   every deposit. ?unused=true for ones not reserving anything
POST /admin/deposits                   add a deposit staff can see in Entrata, by hand
POST /admin/deposits/{id}/refunded     staff refunded it in Entrata, so it can't reserve anymore

Until LiveEntrata is built (app/entrata/client.py), adding deposits by hand is how
students get to reserve.

Staff-only once the Accounts team's login and roles exist.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.db import DbSession
from app.entrata.sync import sync_once
from app.models import Deposit, Reservation
from app.reservations import unit_name, unused_deposits, utcnow
from app.schemas import DepositCreate, DepositOut, SyncSummary

router = APIRouter(tags=["Payments"])


@router.post("/admin/entrata/sync", response_model=SyncSummary)
def sync_now():
    """Look for new security deposits in Entrata, right now."""
    try:
        return sync_once()
    except NotImplementedError as error:
        raise HTTPException(status_code=501, detail=str(error)) from None
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail=str(error)) from None


@router.get("/admin/deposits", response_model=list[DepositOut])
def list_deposits(db: DbSession, unused: bool = False):
    """Deposits, newest first.

    ?unused=true shows the ones that aren't refunded or reserving anything: students
    who paid but haven't reserved yet, roommates, and cancellations that may need a refund.
    """
    query = unused_deposits() if unused else select(Deposit)
    return db.scalars(
        query.options(selectinload(Deposit.reservations)).order_by(
            Deposit.paid_at.desc(), Deposit.id.desc()
        )
    ).all()


@router.post("/admin/deposits", response_model=DepositOut, status_code=201)
def add_deposit(body: DepositCreate, db: DbSession):
    """Staff: I can see this security deposit in Entrata. Let this student reserve."""
    deposit = Deposit(
        entrata_id=body.entrata_id,
        payer_email=body.payer_email.lower(),
        amount_cents=body.amount_cents,
        paid_at=body.paid_at or utcnow(),
    )
    db.add(deposit)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail=f"Entrata payment {body.entrata_id} is already in UnitRes."
        ) from None
    return deposit


@router.post("/admin/deposits/{deposit_id}/refunded", response_model=DepositOut)
def mark_refunded(deposit_id: int, db: DbSession):
    """Staff: I've refunded this deposit in Entrata. It can't reserve anything anymore."""
    deposit = db.get(Deposit, deposit_id, with_for_update=True)
    if deposit is None:
        raise HTTPException(status_code=404, detail="No deposit with that id.")
    if deposit.refunded_at is not None:
        raise HTTPException(status_code=409, detail="That deposit is already marked refunded.")

    in_use = db.scalar(
        select(Reservation).where(
            Reservation.deposit_id == deposit.id, Reservation.status == "confirmed"
        )
    )
    if in_use is not None:
        raise HTTPException(
            status_code=409,
            detail=f"It's paying for {unit_name(in_use)}. Cancel that reservation first.",
        )

    deposit.refunded_at = utcnow()
    db.commit()
    return deposit
