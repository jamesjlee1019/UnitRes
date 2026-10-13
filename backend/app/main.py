"""The API. Every endpoint is listed, and you can try it, at http://localhost:8000/docs"""

from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db import DbSession
from app.models import Apartment
from app.routers import admin, booking, payments

app = FastAPI(title="JSM UnitRes API")

app.include_router(booking.router)
app.include_router(payments.router)
app.include_router(admin.router)


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
    return {"api": "ok", "database": "ok", "apartments": apartment_count}
