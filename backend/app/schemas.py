"""The JSON the API sends and receives.

models.py  = what's stored in the database
schemas.py = what goes over the wire to the website

FastAPI checks incoming JSON against these for you. Try sending
bedrooms: -1 to POST /admin/apartments at http://localhost:8000/docs.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ApartmentOut(BaseModel):
    # Lets a route return a database Apartment directly
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: str
    building: str
    bedrooms: int
    price_cents: int
    available: bool


class ApartmentCreate(BaseModel):
    """What the staff form sends to add an apartment."""

    number: str = Field(min_length=1, max_length=20, examples=["D-410"])
    building: str = Field(min_length=1, max_length=100, examples=["Building D"])
    bedrooms: int = Field(ge=0, le=10, examples=[2])
    price_cents: int = Field(gt=0, examples=[95000])


class ApartmentUpdate(BaseModel):
    """What staff send to change an apartment. Leave out anything that isn't changing."""

    number: str | None = Field(default=None, min_length=1, max_length=20)
    building: str | None = Field(default=None, min_length=1, max_length=100)
    bedrooms: int | None = Field(default=None, ge=0, le=10)
    price_cents: int | None = Field(default=None, gt=0)
    available: bool | None = Field(default=None, examples=[False])


class ReservationCreate(BaseModel):
    """What the website sends when a student clicks Reserve."""

    apartment_id: int
    student_name: str = Field(min_length=1, max_length=200)
    student_email: EmailStr


class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    apartment_id: int
    student_name: str
    student_email: str
    paid: bool
    status: str
    expires_at: datetime | None
    created_at: datetime
