"""Fills an empty database with the same sample data for everyone.

Runs automatically when the api container starts, and only when the apartments
table is empty, so it never overwrites your changes.
To wipe your database and start over: docker compose down -v, then docker compose up
"""

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Apartment, Deposit

def rate_sheet_listing(bedrooms: int, building: str, minimum: int, maximum: int | None = None):
    return {
        "number": f"{bedrooms} bed" if bedrooms else "Studio",
        "building": building,
        "bedrooms": bedrooms,
        "price_cents": minimum * 100,
        "price_max_cents": (maximum or minimum) * 100,
    }


# The 2027-2028 rate sheet lists floor plans by address rather than individual
# unit numbers. Every listed floor plan is shown as available until availability
# is confirmed in Entrata.
AVAILABLE_APARTMENTS = [
    rate_sheet_listing(0, "105 E. Chalmers", 900, 960),
    rate_sheet_listing(0, "105 E. Green", 1190),
    rate_sheet_listing(0, "110 S. Gregory", 815),
    rate_sheet_listing(0, "307 E. Armory", 790, 805),
    rate_sheet_listing(0, "308 E. Armory", 1210),
    rate_sheet_listing(0, "401 E. Chalmers", 865, 885),
    rate_sheet_listing(0, "408 E. Stoughton", 980, 1025),
    rate_sheet_listing(0, "502 E. White", 1170),
    rate_sheet_listing(0, "505 E. Clark", 1075),
    rate_sheet_listing(0, "505 S. Fifth", 1720),
    rate_sheet_listing(0, "507 E. Green", 1425, 1600),
    rate_sheet_listing(0, "602 S. Clark", 925, 1060),
    rate_sheet_listing(0, "902 S. Lincoln", 1110),
    rate_sheet_listing(0, "1103 Euclid", 1180),
    rate_sheet_listing(1, "102 E. Gregory", 1360),
    rate_sheet_listing(1, "105 E. Chalmers", 970, 1080),
    rate_sheet_listing(1, "110 S. Gregory", 856, 960),
    rate_sheet_listing(1, "201 S. Wright", 1350, 1465),
    rate_sheet_listing(1, "203 E. Stoughton", 1139),
    rate_sheet_listing(1, "308 E. Armory", 1440),
    rate_sheet_listing(1, "401 E. Chalmers", 999, 1009),
    rate_sheet_listing(1, "406 E. Clark", 995),
    rate_sheet_listing(1, "408 E. Stoughton", 1170, 1295),
    rate_sheet_listing(1, "505 S. Fifth", 1150, 1995),
    rate_sheet_listing(1, "507 E. Green", 1725, 1915),
    rate_sheet_listing(1, "601 E. White", 1200, 1220),
    rate_sheet_listing(1, "601 S. 6th", 1535, 1660),
    rate_sheet_listing(1, "603 E. White", 1200, 1220),
    rate_sheet_listing(1, "605 E. White", 1200, 1220),
    rate_sheet_listing(1, "607 E. White", 1200, 1220),
    rate_sheet_listing(1, "700 S. Gregory", 1215, 1435),
    rate_sheet_listing(1, "701 S. Gregory", 1210, 1435),
    rate_sheet_listing(1, "707 S. 6th", 1375, 1495),
    rate_sheet_listing(1, "902 S. Lincoln", 1255, 1470),
    rate_sheet_listing(2, "102 E. Gregory", 1790, 1890),
    rate_sheet_listing(2, "105 E. Chalmers", 1570),
    rate_sheet_listing(2, "302 S. 4th", 1690),
    rate_sheet_listing(2, "303 S. Wright", 1690),
    rate_sheet_listing(2, "308 E. Armory", 2000),
    rate_sheet_listing(2, "403 E. White", 1690),
    rate_sheet_listing(2, "408 E. Stoughton", 1710),
    rate_sheet_listing(2, "408 E. White", 1730),
    rate_sheet_listing(2, "502 S. John", 2020),
    rate_sheet_listing(2, "601 S. 6th", 1940, 2160),
    rate_sheet_listing(2, "604 E. Clark", 1520),
    rate_sheet_listing(2, "700 S. Gregory", 1760),
    rate_sheet_listing(2, "701 S. Gregory", 1690),
    rate_sheet_listing(2, "707 S. 6th", 1670, 1970),
    rate_sheet_listing(2, "902 S. Lincoln", 1780, 1880),
    rate_sheet_listing(2, "1103 Euclid", 1850),
    rate_sheet_listing(3, "107 E. Chalmers", 2310),
    rate_sheet_listing(3, "201 E. Healey", 2205),
    rate_sheet_listing(3, "306 E. Armory", 2520, 2625),
    rate_sheet_listing(3, "408 E. White", 2355),
    rate_sheet_listing(3, "501 E. Healey", 2505, 2550),
    rate_sheet_listing(3, "505 E. Healey", 2550),
    rate_sheet_listing(3, "505 S. Fifth", 3300),
    rate_sheet_listing(3, "510 E. Green", 2355),
    rate_sheet_listing(3, "601 S. 6th", 2775, 2820),
    rate_sheet_listing(3, "902 S. Lincoln", 2550),
    rate_sheet_listing(3, "1103 Euclid", 2430),
    rate_sheet_listing(3, "1108 W. Nevada", 2350),
    rate_sheet_listing(4, "102 E. Gregory", 3400),
    rate_sheet_listing(4, "201 E. Healey", 2900),
    rate_sheet_listing(4, "301 S. Water", 2636, 3150),
    rate_sheet_listing(4, "306 E. Armory", 3520),
    rate_sheet_listing(4, "308 E. Armory", 3680),
    rate_sheet_listing(4, "502 S. John", 3500),
    rate_sheet_listing(4, "505 S. Fifth", 4000),
    rate_sheet_listing(4, "508 E. Healey", 3500),
    rate_sheet_listing(4, "508 E. John", 3560),
    rate_sheet_listing(4, "608 E. Green", 3060),
    rate_sheet_listing(4, "608 S. 6th", 3440),
    rate_sheet_listing(4, "616 E. Green", 3840, 3900),
    rate_sheet_listing(4, "1103 Euclid", 3240, 3340),
    rate_sheet_listing(5, "102 E. Gregory", 3925, 4500),
    rate_sheet_listing(5, "306 E. Armory", 4050, 4100),
    rate_sheet_listing(5, "501 E. Healey", 3845),
    rate_sheet_listing(5, "505 E. Healey", 3995),
    rate_sheet_listing(5, "1103 Euclid", 3925),
]

# Has paid a deposit and hasn't reserved yet, so Reserve works for this email right away
PAID_STUDENT_EMAIL = "paid.student@example.com"


def seed() -> None:
    with SessionLocal() as db:
        if db.scalar(select(Apartment).where(Apartment.building == "105 E. Chalmers")):
            print("Seed: rate-sheet apartments already loaded, skipping.")
            return

        existing = db.scalars(select(Apartment)).all()
        for apartment in existing:
            if not apartment.reservations:
                db.delete(apartment)
        db.flush()
        db.add_all([Apartment(**fields) for fields in AVAILABLE_APARTMENTS])

        db.add(
            Deposit(
                entrata_id="SEED-DEPOSIT-2",
                payer_email=PAID_STUDENT_EMAIL,
                amount_cents=50_000,
                paid_at=func.now(),
            )
        )
        db.commit()
        print(f"Seed: loaded {len(AVAILABLE_APARTMENTS)} rate-sheet apartment listings.")


if __name__ == "__main__":
    seed()
