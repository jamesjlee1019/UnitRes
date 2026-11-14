"""The JSON the API sends and receives.

models.py  = what's stored in the database
schemas.py = what goes over the wire to the website

FastAPI checks incoming JSON against these for you. Try sending
bedrooms: -1 to POST /admin/apartments at http://localhost:8000/docs.

If you change one of these, change the matching type in frontend/src/api.ts.
"""

from datetime import datetime
from typing import Literal

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


class ReservationCreate(BaseModel):
    """What the website sends when a student clicks Reserve."""

    model_config = ConfigDict(str_strip_whitespace=True)

    apartment_id: int
    student_name: str = Field(min_length=1, max_length=200)
    # Must be the email they paid the security deposit with in JSM's Entrata,
    # because that's how UnitRes knows they've paid.
    student_email: EmailStr


ReservationStatus = Literal["confirmed", "cancelled"]


class ReservationPublic(BaseModel):
    """What the student sees about their reservation.

    No name or email: there's no login yet, so keep what any one request reveals small.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ReservationStatus
    created_at: datetime
    apartment: ApartmentOut


class Eligibility(BaseModel):
    """Can this student reserve yet? The apartments page asks before showing Reserve."""

    can_reserve: bool
    # ok: they have a deposit that isn't reserving anything yet
    # no_deposit: no security deposit from this email has shown up from Entrata yet
    # already_reserved: their deposit is already paying for a unit (see `reserved`)
    reason: Literal["ok", "no_deposit", "already_reserved"]
    reserved: ReservationPublic | None
    # Where to send them to apply and pay, when they haven't yet
    entrata_application_url: str


class DepositSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entrata_id: str
    amount_cents: int
    paid_at: datetime


class ReservationOut(BaseModel):
    """A full reservation, for staff."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    apartment_id: int
    student_name: str
    student_email: str
    status: ReservationStatus
    created_at: datetime
    entrata_unit_marked: bool
    apartment: ApartmentOut
    # Only empty on cancelled reservations from before the Entrata handoff
    deposit: DepositSummary | None


class DepositOut(BaseModel):
    """A security deposit, for staff."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    entrata_id: str
    payer_email: str
    amount_cents: int
    paid_at: datetime
    received_at: datetime
    refunded_at: datetime | None
    # The confirmed reservation it's paying for. Empty means it can still reserve a unit
    # (unless it's been refunded).
    active_reservation_id: int | None


class DepositCreate(BaseModel):
    """Staff adding a deposit they can see in Entrata, before the sync job can read Entrata."""

    model_config = ConfigDict(str_strip_whitespace=True)

    entrata_id: str = Field(
        min_length=1,
        max_length=100,
        description="The payment or receipt number in Entrata",
        examples=["1234567"],
    )
    payer_email: EmailStr = Field(description="The email on the student's Entrata application")
    amount_cents: int = Field(gt=0, examples=[50000])
    paid_at: datetime | None = Field(default=None, description="Leave empty for now")


class SyncSummary(BaseModel):
    """What one run of the Entrata sync did."""

    new_deposits: int
    already_seen: int
    # Application fees and anything else that isn't a security deposit
    not_deposits: int


class FakeDepositIn(BaseModel):
    """Development only: pretend a student paid something in Entrata."""

    email: EmailStr
    kind: Literal["security_deposit", "application_fee"] = "security_deposit"
    amount_cents: int | None = Field(
        default=None, gt=0, description="Leave empty for a typical amount"
    )
