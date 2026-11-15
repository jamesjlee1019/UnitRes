"""The API. Every endpoint is listed, and you can try it, at http://localhost:8000/docs"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.db import DbSession
from app.jobs import start_entrata_sync
from app.models import Apartment
from app.routers import admin, applications, booking, dev, payments

# So our own log lines (unitres.*) show up in "docker compose logs -f api"
_log = logging.getLogger("unitres")
_log.setLevel(logging.INFO)
if not _log.handlers:
    _log.addHandler(logging.StreamHandler())


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    stop_sync = None
    if settings.entrata_poll_seconds > 0:
        stop_sync = start_entrata_sync(settings.entrata_poll_seconds)
    yield
    if stop_sync:
        stop_sync()


app = FastAPI(title="JSM UnitRes API", lifespan=lifespan)

app.include_router(booking.router)
app.include_router(applications.router)
app.include_router(payments.router)
app.include_router(admin.router)
if settings.entrata_mode == "fake":
    # Pretend-Entrata controls. Never reachable when talking to the real Entrata.
    app.include_router(dev.router)

@app.get("/health", tags=["Setup"])
def health(db: DbSession):
    """Lets the home page check that the API and the database are up.

    It's also a working example of a database query: build it with select(),
    then run it with db.scalar() for one value or db.scalars(...).all() for a list.
    """
    try:
        apartment_count = db.scalar(select(func.count()).select_from(Apartment))
    except SQLAlchemyError as error:
        return {"api": "ok", "database": "error", "detail": str(error.__cause__ or error)}
    return {
        "api": "ok",
        "database": "ok",
        "apartments": apartment_count,
        "entrata_mode": settings.entrata_mode,
    }
