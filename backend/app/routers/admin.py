"""ADMIN TEAM: the staff back office.

GET    /admin/apartments                            every apartment, including unavailable ones
POST   /admin/apartments                            add an apartment
PATCH  /admin/apartments/{id}                       change one, like marking it unavailable
DELETE /admin/apartments/{id}                       remove one, unless it has reservations
GET    /admin/reservations                          who reserved what
POST   /admin/reservations/{id}/cancel              cancel a reservation
DELETE /admin/reservations/{id}                     delete a cancelled reservation
POST   /admin/reservations/{id}/entrata-updated     staff made Entrata match this reservation

Deposits (paid, unused, refunded) are in app/routers/payments.py.

Money and units live in Entrata too, and UnitRes can only read it. So when something
changes here, staff make the same change in Entrata, and these routes record that they did:
  - reserved → mark the unit as taken in Entrata, so nobody leases it there
  - cancelled → put it back on the market in Entrata

Later, only staff should be able to reach these routes. The Accounts team's
login and roles will plug in here.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app import events
from app.db import DbSession
from app.models import Apartment, Reservation
from app.schemas import ApartmentCreate, ApartmentOut, ApartmentUpdate, ReservationOut

router = APIRouter(tags=["Admin"])


@router.get("/admin/apartments", response_model=list[ApartmentOut])
def list_all_apartments(db: DbSession):
    """Staff: show me every apartment, including ones that aren't available."""
    return db.scalars(select(Apartment).order_by(Apartment.building, Apartment.number)).all()


@router.post("/admin/apartments", response_model=ApartmentOut, status_code=201)
def add_apartment(apartment: ApartmentCreate, db: DbSession):
    """Staff: add an apartment."""
    # FastAPI has already checked the input against ApartmentCreate,
    # so its fields can go straight into a new database row.
    new_apartment = Apartment(**apartment.model_dump())
    db.add(new_apartment)
    try:
        db.commit()
    except IntegrityError:
        # The database refused it because that building already has this unit
        # number (apartment_unit_is_unique in models.py). 409 means "Conflict".
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{apartment.building} already has a unit {apartment.number}.",
        )
    # The database assigns the id on commit. response_model=ApartmentOut
    # turns the row into JSON.
    return new_apartment


@router.patch("/admin/apartments/{apartment_id}", response_model=ApartmentOut)
def update_apartment(apartment_id: int, changes: ApartmentUpdate, db: DbSession):
    """Staff: change an apartment, e.g. {"available": false} to take it off the market."""
    apartment = db.get(Apartment, apartment_id)
    if apartment is None:
        raise HTTPException(status_code=404, detail="Apartment not found")
    # Only the fields staff sent are changed. None isn't allowed in any column,
    # so a field sent as null is skipped too.
    for field, value in changes.model_dump(exclude_none=True).items():
        setattr(apartment, field, value)
    try:
        db.commit()
    except IntegrityError:
        # Renamed it to a unit number its building already has
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"{apartment.building} already has a unit {apartment.number}.",
        )
    return apartment


@router.delete("/admin/apartments/{apartment_id}", status_code=204)
def remove_apartment(apartment_id: int, db: DbSession):
    """Staff: remove an apartment."""
    apartment = db.get(Apartment, apartment_id)
    if apartment is None:
        raise HTTPException(status_code=404, detail="Apartment not found")
    # Reservations point at the apartment, so deleting it would break them
    # (and the database refuses anyway). Staff can mark it unavailable instead.
    if apartment.reservations:
        raise HTTPException(
            status_code=409,
            detail="Apartment has reservations and can't be removed. Mark it unavailable instead.",
        )
    db.delete(apartment)
    db.commit()


@router.get("/admin/reservations", response_model=list[ReservationOut])
def list_reservations(db: DbSession):
    """Staff: show me all reservations."""
    # selectinload gets each reservation's apartment and deposit in the same trip
    # to the database, since ReservationOut includes both.
    reservations = db.scalars(
        select(Reservation)
        .options(selectinload(Reservation.apartment), selectinload(Reservation.deposit))
        .order_by(Reservation.id)
    ).all()
    return reservations


def _get_for_update(db: DbSession, reservation_id: int) -> Reservation:
    reservation = db.get(Reservation, reservation_id, with_for_update=True)
    if reservation is None:
        raise HTTPException(status_code=404, detail="No reservation with that id.")
    return reservation


@router.post("/admin/reservations/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_reservation(reservation_id: int, db: DbSession):
    """Staff: cancel a reservation. The unit goes back on the list.

    The student's deposit is free again: they can reserve another unit with it, or
    staff refund it in Entrata and mark it refunded (POST /admin/deposits/{id}/refunded).
    """
    reservation = _get_for_update(db, reservation_id)
    if reservation.status != "confirmed":
        raise HTTPException(
            status_code=409, detail=f"That reservation is already {reservation.status}."
        )

    reservation.status = "cancelled"
    db.commit()

    events.fire("reservation_cancelled", reservation.id)
    return reservation


@router.post("/admin/reservations/{reservation_id}/entrata-updated", response_model=ReservationOut)
def entrata_updated(reservation_id: int, db: DbSession):
    """Staff: I've made Entrata match this reservation.

    Confirmed → the unit is now marked as taken in Entrata.
    Cancelled → the unit is back on the market in Entrata.
    """
    reservation = _get_for_update(db, reservation_id)
    reservation.entrata_unit_marked = reservation.status == "confirmed"
    db.commit()
    return reservation


@router.delete("/admin/reservations/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: int, db: DbSession):
    """Staff: delete a cancelled reservation, e.g. to clear it before removing the apartment.

    A confirmed reservation is a student's unit, so cancel it first. Deleting doesn't
    touch the deposit: it shows up in GET /admin/deposits?unused=true for a refund.
    """
    reservation = _get_for_update(db, reservation_id)
    if reservation.status == "confirmed":
        raise HTTPException(
            status_code=409,
            detail="This reservation is confirmed. Cancel it before deleting it.",
        )
    db.delete(reservation)
    db.commit()
