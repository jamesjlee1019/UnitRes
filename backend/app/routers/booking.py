"""BOOKING TEAM: listings, availability, and temporary reservations."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db import DbSession
from app.models import Apartment, Reservation
from app.schemas import ApartmentOut, ReservationCreate, ReservationOut

router = APIRouter(tags=["Booking"])
HOLD_TTL = timedelta(minutes=30)


@router.get("/apartments", response_model=list[ApartmentOut])
def list_available_apartments(db: DbSession):
    """Return apartments that are available to reserve."""
    return db.scalars(select(Apartment).where(Apartment.available.is_(True))).all()


@router.post("/reservations", response_model=ReservationOut, status_code=201)
def reserve_apartment(reservation: ReservationCreate, db: DbSession):
    """Create a 30-minute hold for an available apartment."""
    now = datetime.now(UTC)

    # Lock the apartment so simultaneous requests cannot create two holds.
    apartment = db.scalar(
        select(Apartment)
        .where(Apartment.id == reservation.apartment_id)
        .with_for_update()
    )
    if apartment is None:
        raise HTTPException(status_code=404, detail="Apartment not found.")

    existing_hold = db.scalar(
        select(Reservation)
        .where(
            Reservation.apartment_id == apartment.id,
            Reservation.status == "held",
        )
        .with_for_update()
    )
    if existing_hold is not None:
        if existing_hold.expires_at is not None and existing_hold.expires_at > now:
            raise HTTPException(
                status_code=409,
                detail="This apartment is currently being reserved.",
            )

        existing_hold.status = "expired"
        apartment.available = True

    if not apartment.available:
        raise HTTPException(
            status_code=409,
            detail="This apartment is no longer available.",
        )

    held_reservation = Reservation(
        **reservation.model_dump(),
        status="held",
        expires_at=now + HOLD_TTL,
    )
    apartment.available = False
    db.add(held_reservation)
    db.commit()
    db.refresh(held_reservation)
    return held_reservation
