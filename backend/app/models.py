"""The database tables. This file is the schema from kickoff slide 4, plus what the
Entrata handoff needs (migration 0003).

Changing a table means editing this file AND adding a migration,
or nobody else's database will match. See "Changing the schema" in the README.
"""

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Date,
    false,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Apartment(Base):
    __tablename__ = "apartments"
    __table_args__ = (
        # A building can't have the same unit number twice
        UniqueConstraint("building", "number", name="apartment_unit_is_unique"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20))  # "A-101"
    building: Mapped[str] = mapped_column(String(100))  # "Building A"
    bedrooms: Mapped[int]
    price_cents: Mapped[int]  # monthly rent in cents, so 72500 means $725.00
    price_max_cents: Mapped[int | None] = mapped_column(nullable=True)
    # Staff's switch for "this unit is on the market". A unit with a confirmed
    # reservation also drops off the student list, even when this is True.
    available: Mapped[bool] = mapped_column(default=True, server_default=true())

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="apartment")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str] = mapped_column(String(30))
    school: Mapped[str] = mapped_column(String(200))
    move_in_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Deposit(Base):
    """A security deposit a student paid in JSM's Entrata.

    The sync job copies them in from Entrata (or staff add one by hand). A deposit is
    what lets a student reserve: each one can back one confirmed reservation at a time.
    """

    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Entrata's ID for the payment. Unique, so syncing twice never adds it twice.
    entrata_id: Mapped[str] = mapped_column(String(100), unique=True)
    # Stored lowercase. The student reserves with this same email.
    payer_email: Mapped[str] = mapped_column(String(320), index=True)
    amount_cents: Mapped[int]
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Staff refunded it in Entrata, so it can't reserve anything anymore
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="deposit")

    @property
    def active_reservation_id(self) -> int | None:
        """The confirmed reservation this deposit is paying for, if any."""
        return next((r.id for r in self.reservations if r.status == "confirmed"), None)


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('confirmed', 'cancelled')",
            name="reservation_status_is_valid",
        ),
        # Every confirmed reservation is paid for. (Only cancelled ones from
        # before the Entrata handoff have no deposit.)
        CheckConstraint(
            "status = 'cancelled' OR deposit_id IS NOT NULL",
            name="confirmed_reservation_has_deposit",
        ),
        # Booking's hard question (slide 8, option B): one confirmed reservation per unit.
        # If two students reserve the same unit at the same moment, the database
        # accepts the first insert and rejects the second.
        Index(
            "one_active_reservation_per_apartment",
            "apartment_id",
            unique=True,
            postgresql_where=text("status = 'confirmed'"),
        ),
        # And one confirmed reservation per deposit, so one deposit can't reserve two
        # units, even if the student clicks Reserve on two at once.
        Index(
            "one_active_reservation_per_deposit",
            "deposit_id",
            unique=True,
            postgresql_where=text("status = 'confirmed'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    apartment_id: Mapped[int] = mapped_column(ForeignKey("apartments.id"))
    student_name: Mapped[str] = mapped_column(String(200))
    # Stored lowercase. The same email they paid the deposit with in Entrata.
    student_email: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(
        String(20), default="confirmed", server_default="confirmed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # The deposit paying for it
    deposit_id: Mapped[int | None] = mapped_column(ForeignKey("deposits.id"))
    # Staff have marked the unit as taken in Entrata too. Until they do, someone could
    # still lease it through jsmliving.com.
    entrata_unit_marked: Mapped[bool] = mapped_column(default=False, server_default=false())

    apartment: Mapped[Apartment] = relationship(back_populates="reservations")
    deposit: Mapped[Deposit | None] = relationship(back_populates="reservations")


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("role IN ('student', 'faculty')", name="user_role_is_valid",),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="student", server_default="student")
