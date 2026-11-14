"""Admin: adding apartments from the staff page.

These tests add apartments to your real database, so each one uses a made-up
unit number and deletes what it added when it's done.
"""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db import SessionLocal
from app.main import app
from app.models import Apartment

client = TestClient(app)

TEST_BUILDING = "Test Building"


def make_unit(building: str = TEST_BUILDING) -> dict:
    return {
        "number": f"T-{uuid4().hex[:6]}",  # a number no real unit has
        "building": building,
        "bedrooms": 1,
        "price_cents": 50_000,
    }


def delete_test_units(number: str) -> None:
    with SessionLocal() as db:
        db.execute(delete(Apartment).where(Apartment.number == number))
        db.commit()


def test_adding_the_same_unit_twice_is_rejected():
    unit = make_unit()
    try:
        assert client.post("/admin/apartments", json=unit).status_code == 201

        again = client.post("/admin/apartments", json=unit)
        assert again.status_code == 409
        assert unit["number"] in again.json()["detail"]
    finally:
        delete_test_units(unit["number"])


def test_same_unit_number_in_another_building_is_fine():
    unit = make_unit()
    other_building = {**unit, "building": "Test Building 2"}
    try:
        assert client.post("/admin/apartments", json=unit).status_code == 201
        assert client.post("/admin/apartments", json=other_building).status_code == 201
    finally:
        delete_test_units(unit["number"])


def test_rent_over_the_limit_is_rejected():
    # $30 million a month. This used to crash the API instead of returning an error.
    unit = {**make_unit(), "price_cents": 3_000_000_000}
    assert client.post("/admin/apartments", json=unit).status_code == 422


def test_renaming_a_unit_to_one_that_exists_is_rejected():
    unit = make_unit()
    other = make_unit()
    try:
        assert client.post("/admin/apartments", json=unit).status_code == 201
        other_id = client.post("/admin/apartments", json=other).json()["id"]

        renamed = client.patch(f"/admin/apartments/{other_id}", json={"number": unit["number"]})
        assert renamed.status_code == 409
    finally:
        delete_test_units(unit["number"])
        delete_test_units(other["number"])


def test_editing_rent_over_the_limit_is_rejected():
    unit = make_unit()
    try:
        unit_id = client.post("/admin/apartments", json=unit).json()["id"]
        too_much = client.patch(f"/admin/apartments/{unit_id}", json={"price_cents": 3_000_000_000})
        assert too_much.status_code == 422
    finally:
        delete_test_units(unit["number"])
