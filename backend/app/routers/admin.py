"""ADMIN TEAM: the staff back office.

Week 1: POST /admin/apartments adds an apartment to the database,
and the form at http://localhost:3000/admin sends to it.

Later, only staff should be able to reach these routes. The Accounts team's
login and roles will plug in here.
"""

from fastapi import APIRouter

from app.db import DbSession
from app.models import Apartment  # noqa: F401  (you'll need this)
from app.routers import not_built_yet
from app.schemas import ApartmentCreate, ApartmentOut, ReservationOut

router = APIRouter(tags=["Admin"])


@router.post("/admin/apartments", response_model=ApartmentOut, status_code=201)
def add_apartment(apartment: ApartmentCreate, db: DbSession):
    """Staff: add an apartment."""
    # TODO (Admin, week 1): make an Apartment from `apartment`, add it to `db`,
    # commit, and return it. FastAPI has already checked the input for you.
    raise not_built_yet("Admin", "backend/app/routers/admin.py")


@router.delete("/admin/apartments/{apartment_id}", status_code=204)
def remove_apartment(apartment_id: int, db: DbSession):
    """Staff: remove an apartment."""
    # TODO (Admin, week 2): what should happen if the unit already has reservations?
    raise not_built_yet("Admin", "backend/app/routers/admin.py")


@router.get("/admin/reservations", response_model=list[ReservationOut])
def list_reservations(db: DbSession):
    """Staff: show me all reservations."""
    # TODO (Admin, week 2): the seed data has one reservation to show.
    raise not_built_yet("Admin", "backend/app/routers/admin.py")
