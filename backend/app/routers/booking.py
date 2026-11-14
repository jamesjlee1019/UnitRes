"""BOOKING TEAM: listings, availability, reserving.

GET  /apartments                    the units a student can reserve right now
GET  /eligibility?email=...         has this student paid, so Reserve should be on?
POST /reservations                  reserve a unit. It's confirmed right away.

No holds. Students apply and pay the security deposit in JSM's Entrata first.
Once the sync job has seen the deposit, Reserve works for that email, and reserving
is instant: the unit is theirs and leaves the list. One deposit reserves one unit.

Two students, one unit, same second (kickoff slide 8): the database settles it.
The "one_active_reservation_per_apartment" index in app/models.py lets only one
confirmed reservation exist per unit, so the second insert fails and that student
gets a 409 "just taken". Their deposit wasn't used, so they just pick another unit.
tests/test_reservations.py fires two at once to prove it.

When the Accounts team's login exists, use the logged-in student's (verified) email
instead of one typed into a form. Until then, anyone who knows a paid student's email
could reserve with their deposit.
"""

from fastapi import APIRouter, HTTPException
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import events
from app.config import settings
from app.db import DbSession
from app.models import Apartment, Reservation
from app.reservations import (
    confirmed_reservation_for,
    unit_name,
    unused_deposit_for,
    violated_constraint,
)
from app.schemas import ApartmentOut, Eligibility, ReservationCreate, ReservationPublic

router = APIRouter(tags=["Booking"])


@router.get("/apartments", response_model=list[ApartmentOut])
def list_available_apartments(db: DbSession):
    """Give me all available apartments: on the market, and nobody has reserved them."""
    taken = select(Reservation.id).where(
        Reservation.apartment_id == Apartment.id, Reservation.status == "confirmed"
    )
    return db.scalars(
        select(Apartment)
        .where(Apartment.available.is_(True), ~taken.exists())
        .order_by(Apartment.building, Apartment.number)
    ).all()


@router.get("/eligibility", response_model=Eligibility)
def can_reserve(email: EmailStr, db: DbSession):
    """Can this student reserve? Turn the Reserve buttons on only when can_reserve is true.

    A deposit can take a few minutes (ENTRATA_POLL_SECONDS) to show up after they pay,
    so the page can ask again every so often while it says "waiting for your deposit".
    """
    email = email.lower()
    if unused_deposit_for(db, email) is not None:
        return Eligibility(
            can_reserve=True,
            reason="ok",
            reserved=None,
            entrata_application_url=settings.entrata_application_url,
        )
    reserved = confirmed_reservation_for(db, email)
    return Eligibility(
        can_reserve=False,
        reason="already_reserved" if reserved else "no_deposit",
        reserved=ReservationPublic.model_validate(reserved) if reserved else None,
        entrata_application_url=settings.entrata_application_url,
    )


@router.post("/reservations", response_model=ReservationPublic, status_code=201)
def reserve_apartment(reservation: ReservationCreate, db: DbSession):
    """Reserve this apartment for this student, using their security deposit.

    402 if no unused deposit from this email has shown up from Entrata yet.
    409 if someone else just reserved the unit, or their deposit is already used.
    """
    email = reservation.student_email.lower()

    apartment = db.get(Apartment, reservation.apartment_id)
    if apartment is None or not apartment.available:
        raise HTTPException(status_code=404, detail="That apartment isn't available to reserve.")

    deposit = unused_deposit_for(db, email, lock=True)
    if deposit is None:
        already = confirmed_reservation_for(db, email)
        if already is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"{email} has already reserved {unit_name(already)}. "
                    "One security deposit reserves one unit."
                ),
            )
        raise HTTPException(
            status_code=402,
            detail=(
                f"We haven't seen a security deposit from {email} yet. Apply and pay it in "
                "JSM's application using this email, then come back to reserve. "
                "It can take a few minutes to show up here."
            ),
        )

    new_reservation = Reservation(
        apartment=apartment,
        student_name=reservation.student_name,
        student_email=email,
        status="confirmed",
        deposit=deposit,
    )
    db.add(new_reservation)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        constraint = violated_constraint(error)
        if constraint == "one_active_reservation_per_apartment":
            raise HTTPException(
                status_code=409,
                detail="Sorry, someone just reserved this unit. Your deposit wasn't used, so pick another.",
            ) from None
        if constraint == "one_active_reservation_per_deposit":
            raise HTTPException(
                status_code=409,
                detail="Your deposit was just used to reserve another unit.",
            ) from None
        raise

    events.fire("reservation_confirmed", new_reservation.id)
    return new_reservation
