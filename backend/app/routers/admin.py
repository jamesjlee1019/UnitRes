"""ADMIN TEAM: the staff back office.

Week 1: POST /admin/apartments adds an apartment to the database,
and the form at http://localhost:3000/admin sends to it.

Later, only staff should be able to reach these routes. The Accounts team's
login and roles will plug in here.
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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


@router.delete("/admin/apartments/{apartment_id}", status_code=204)
def remove_apartment(apartment_id: int, db: DbSession):
    """Staff: remove an apartment."""
    # TODO (Admin, week 2): what should happen if the unit already has reservations?
    raise not_built_yet("Admin", "backend/app/routers/admin.py")


@router.get("/admin/reservations", response_model=list[ReservationOut])
def list_reservations(db: DbSession):
    """Staff: show me all reservations."""
    # TODO (Admin, week 2): the seed data has one reservation to show.
    reservations = db.scalars(select(Reservation).order_by(Reservation.id)).all()
    return reservations
