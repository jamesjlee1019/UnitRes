"""BOOKING TEAM: listings, availability, reserving.

Week 1: GET /apartments returns the available apartments from the database,
and the page at http://localhost:3000/apartments shows them.

How to query the database: the /health route in app/main.py is a working example.
SQLAlchemy's guide to select(): https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
"""

from fastapi import APIRouter
from sqlalchemy import select  # noqa: F401  (you'll need these two imports)

from app.db import DbSession
from app.models import Apartment
from app.routers import not_built_yet
from app.schemas import ApartmentOut, ReservationCreate, ReservationOut

router = APIRouter(tags=["Booking"])


@router.get("/apartments", response_model=list[ApartmentOut])
def list_available_apartments(db: DbSession):
    """Give me all available apartments."""
    return db.scalars(select(Apartment).where(Apartment.available.is_(True))).all()


@router.post("/reservations", response_model=ReservationOut, status_code=201)
def reserve_apartment(reservation: ReservationCreate, db: DbSession):
    """Reserve this apartment for this student."""
    # TODO (Booking, week 2): create a "held" reservation. If two students click
    # Reserve on the same unit at the same moment, only one can get it.
    raise not_built_yet("Booking", "backend/app/routers/booking.py")
