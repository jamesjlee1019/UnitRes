"""The database tables. This file is the schema from kickoff slide 4.

Changing a table means editing this file AND adding a migration,
or nobody else's database will match. See "Changing the schema" in the README.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, false, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Apartment(Base):
    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20))  # "A-101"
    building: Mapped[str] = mapped_column(String(100))  # "Building A"
    bedrooms: Mapped[int]
    price_cents: Mapped[int]  # monthly rent in cents, so 72500 means $725.00
    available: Mapped[bool] = mapped_column(default=True, server_default=true())

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="apartment")


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        # The four states from kickoff slide 7
        CheckConstraint(
            "status IN ('held', 'confirmed', 'expired', 'cancelled')",
            name="reservation_status_is_valid",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    apartment_id: Mapped[int] = mapped_column(ForeignKey("apartments.id"))
    student_name: Mapped[str] = mapped_column(String(200))
    student_email: Mapped[str] = mapped_column(String(320))
    paid: Mapped[bool] = mapped_column(default=False, server_default=false())
    status: Mapped[str] = mapped_column(String(20), default="held", server_default="held")
    # When a "held" reservation runs out. Empty once it's confirmed.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    apartment: Mapped[Apartment] = relationship(back_populates="reservations")
