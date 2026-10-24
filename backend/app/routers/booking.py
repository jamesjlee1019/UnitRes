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
    """BOOKING TEAM: listings, availability, reserving.

Week 1: GET /apartments returns the available apartments from the database,
and the page at http://localhost:3000/apartments shows them.

How to query the database: the /health route in app/main.py is a working example.
SQLAlchemy's guide to select(): https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
"""

from fastapi import APIRouter
from sqlalchemy import select  # noqa: F401  (you'll need these two imports)

from app.db import DbSession
from app.models import Apartment, Reservation  # noqa: F401
from app.routers import not_built_yet
from app.schemas import ApartmentOut, ReservationCreate, ReservationOut

router = APIRouter(tags=["Booking"])


@router.get("/apartments", response_model=list[ApartmentOut])
def list_available_apartments(db: DbSession):
    """Give me all available apartments."""
    # TODO (Booking, week 1): return the apartments where `available` is true.
    # Something like: db.scalars(select(Apartment).where(...)).all()
    # The seed data has 5 apartments and 4 are available,
    # so if your page shows 5, the filter isn't working yet.
    return db.scalars(select(Apartment).where(Apartment.available.is_(True))).all()


@router.post("/reservations", response_model=ReservationOut, status_code=201)
def reserve_apartment(reservation: ReservationCreate, db: DbSession):
    # TODO (Booking, week 2): create a "held" reservation. If two students click
    # Reserve on the same unit at the same moment, only one can get it.
    """Create a time-limited hold for an available apartment."""
    """Create a 30-minute hold for an available apartment."""
    now = datetime.now(UTC)

    # Lock this apartment until the transaction finishes so only one
    # simultaneous reservation request can succeed.
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
        # An active hold blocks another reservation.
        if existing_hold.hold_expires_at > now:
            raise HTTPException(
                status_code=409,
                detail="This apartment is currently being reserved.",
            )

        # The 30-minute window passed without payment.
        existing_hold.status = "expired"

    elif not apartment.available:
        # The apartment is unavailable for another reason, such as a
        # confirmed/paid reservation.
        raise HTTPException(
            status_code=409,
            detail="This apartment is no longer available.",
        )

    held_reservation = Reservation(
        **reservation.model_dump(),
        status="held",
        hold_expires_at=now + HOLD_TTL,
    )

    apartment.available = False

    db.add(held_reservation)
    db.commit()
    db.refresh(held_reservation)

    return held_reservation
