"""ADMIN TEAM: the staff back office.

POST   /admin/apartments                            add an apartment (week 1)
DELETE /admin/apartments/{id}                       remove one (TODO below)
GET    /admin/reservations                          who reserved what
POST   /admin/reservations/{id}/cancel              cancel a reservation
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
from sqlalchemy.orm import selectinload

from app import events
from app.db import DbSession
from app.models import Apartment, Reservation
from app.routers import not_built_yet
from app.schemas import ApartmentCreate, ApartmentOut, ReservationOut

router = APIRouter(tags=["Admin"])


@router.post("/admin/apartments", response_model=ApartmentOut, status_code=201)
def add_apartment(apartment: ApartmentCreate, db: DbSession):
    """Staff: add an apartment."""
    # FastAPI has already checked the input against ApartmentCreate,
    # so its fields can go straight into a new database row.
    new_apartment = Apartment(**apartment.model_dump())
    db.add(new_apartment)
    db.commit()
    # The database assigns the id on commit. response_model=ApartmentOut
    # turns the row into JSON.
    return new_apartment


@router.delete("/admin/apartments/{apartment_id}", status_code=204)
def remove_apartment(apartment_id: int, db: DbSession):
    """Staff: remove an apartment."""
    # TODO (Admin): what should happen if the unit already has reservations?
    raise not_built_yet("Admin", "backend/app/routers/admin.py")


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
