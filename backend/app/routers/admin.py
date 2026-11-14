"""ADMIN TEAM: the staff back office.

Week 1: POST /admin/apartments adds an apartment to the database,
and the form at http://localhost:3000/admin sends to it.

Week 2: GET /admin/apartments lists every apartment, DELETE removes one,
and GET /admin/reservations lists who reserved what.

Next: PATCH /admin/apartments/{id} changes an apartment, like marking it
unavailable when it can't be removed.

Later, only staff should be able to reach these routes. The Accounts team's
login and roles will plug in here.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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
    db.commit()
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
    # TODO (Admin, week 2): the seed data has one reservation to show.
    reservations = db.scalars(select(Reservation).order_by(Reservation.id)).all()
    return reservations

@router.delete("/admin/reservations/{reservation_id}", status_code=204)
def delete_reservation(reservation_id: int, db: DbSession):
    """Staff: delete an unpaid reservation."""
    reservation = db.get(Reservation, reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found.")
    if reservation.paid:
        raise HTTPException(
            status_code=409,
            detail="This reservation is paid. Refund it in Stripe before deleting.",
        )
    db.delete(reservation)
    db.commit()