"""Reserving: pay the deposit in Entrata first, then Reserve is instant. No holds.

Run from the repo root:  docker compose exec api pytest
"""

import threading

import pytest
from fastapi.testclient import TestClient

from app import events
from app.db import SessionLocal
from app.entrata.client import fake_entrata
from app.entrata.sync import sync_once
from app.main import app
from app.models import Apartment, Deposit
from app.seed import PAID_STUDENT_EMAIL, seed

client = TestClient(app)


@pytest.fixture
def units() -> list[int]:
    with SessionLocal() as db:
        apartments = [
            Apartment(number="A-101", building="Building A", bedrooms=1, price_cents=72_500),
            Apartment(number="A-204", building="Building A", bedrooms=2, price_cents=85_000),
            Apartment(
                number="Z-999", building="Building Z", bedrooms=1, price_cents=1, available=False
            ),
        ]
        db.add_all(apartments)
        db.commit()
        return [a.id for a in apartments]


@pytest.fixture
def fired(monkeypatch) -> list[tuple[str, int]]:
    """Every event fired during the test."""
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(events, "fire", lambda name, rid: calls.append((name, rid)))
    return calls


def pay_deposit(email: str) -> None:
    response = client.post("/dev/entrata/payments", json={"email": email})
    assert response.status_code == 200, response.text


def reserve(apartment_id: int, email: str, test_client: TestClient = client):
    return test_client.post(
        "/reservations",
        json={"apartment_id": apartment_id, "student_name": "Sam Student", "student_email": email},
    )


def eligibility(email: str) -> dict:
    response = client.get("/eligibility", params={"email": email})
    assert response.status_code == 200, response.text
    return response.json()


def listed_ids() -> set[int]:
    return {a["id"] for a in client.get("/apartments").json()}


def test_reserve_without_a_deposit_is_refused(units):
    assert eligibility("sam@example.com")["reason"] == "no_deposit"

    response = reserve(units[0], "sam@example.com")

    assert response.status_code == 402
    assert units[0] in listed_ids()  # nothing was held


def test_application_fee_alone_does_not_unlock_reserve(units):
    client.post(
        "/dev/entrata/payments", json={"email": "sam@example.com", "kind": "application_fee"}
    )

    assert eligibility("sam@example.com")["can_reserve"] is False
    assert reserve(units[0], "sam@example.com").status_code == 402


def test_after_paying_reserve_is_confirmed_right_away(units, fired):
    pay_deposit("Sam@Example.com")
    assert eligibility("sam@example.com") | {"entrata_application_url": None} == {
        "can_reserve": True,
        "reason": "ok",
        "reserved": None,
        "entrata_application_url": None,
    }

    response = reserve(units[0], "SAM@example.com ")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["apartment"]["id"] == units[0]
    assert units[0] not in listed_ids()
    assert fired == [("reservation_confirmed", body["id"])]

    after = eligibility("sam@example.com")
    assert after["reason"] == "already_reserved"
    assert after["reserved"]["apartment"]["id"] == units[0]


def test_one_deposit_reserves_one_unit(units):
    pay_deposit("sam@example.com")
    assert reserve(units[0], "sam@example.com").status_code == 201

    response = reserve(units[1], "sam@example.com")

    assert response.status_code == 409
    assert "already reserved" in response.json()["detail"]
    assert units[1] in listed_ids()


def test_unavailable_or_missing_apartment(units):
    pay_deposit("sam@example.com")
    assert reserve(units[2], "sam@example.com").status_code == 404  # staff took it off the market
    assert reserve(123456, "sam@example.com").status_code == 404
    assert eligibility("sam@example.com")["can_reserve"] is True  # deposit still unused


def reserve_at_the_same_moment(requests: list[tuple[int, str]]) -> list[int]:
    """Fire every (apartment_id, email) reservation at once. Returns the status codes."""
    start = threading.Barrier(len(requests))
    codes: list[int] = [0] * len(requests)

    def go(i: int, apartment_id: int, email: str) -> None:
        own_client = TestClient(app)
        start.wait()
        codes[i] = reserve(apartment_id, email, own_client).status_code

    threads = [threading.Thread(target=go, args=(i, *r)) for i, r in enumerate(requests)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return sorted(codes)


def test_two_paid_students_one_unit_same_moment(units):
    pay_deposit("first@example.com")
    pay_deposit("second@example.com")

    codes = reserve_at_the_same_moment(
        [(units[0], "first@example.com"), (units[0], "second@example.com")]
    )

    assert codes == [201, 409]
    staff_view = client.get("/admin/reservations").json()
    assert len(staff_view) == 1
    # Whoever lost still has their deposit, and can pick another unit
    loser = ({"first@example.com", "second@example.com"} - {staff_view[0]["student_email"]}).pop()
    assert eligibility(loser)["can_reserve"] is True
    assert reserve(units[1], loser).status_code == 201


def test_one_deposit_two_units_same_moment(units):
    pay_deposit("sam@example.com")

    codes = reserve_at_the_same_moment(
        [(units[0], "sam@example.com"), (units[1], "sam@example.com")]
    )

    assert codes == [201, 409]
    assert len(client.get("/admin/reservations").json()) == 1
    assert len(listed_ids() & {units[0], units[1]}) == 1  # the other unit is still listed


def test_cancel_puts_the_unit_back_and_frees_the_deposit(units, fired):
    pay_deposit("sam@example.com")
    reservation_id = reserve(units[0], "sam@example.com").json()["id"]

    response = client.post(f"/admin/reservations/{reservation_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert ("reservation_cancelled", reservation_id) in fired
    assert units[0] in listed_ids()
    unused = client.get("/admin/deposits", params={"unused": True}).json()
    assert [d["payer_email"] for d in unused] == ["sam@example.com"]
    # Same deposit, different unit
    assert reserve(units[1], "sam@example.com").status_code == 201
    assert client.post(f"/admin/reservations/{reservation_id}/cancel").status_code == 409


def test_staff_add_deposit_by_hand_then_refund_it(units):
    new = {"entrata_id": "1234567", "payer_email": "Sam@Example.com", "amount_cents": 50_000}
    response = client.post("/admin/deposits", json=new)
    assert response.status_code == 201, response.text
    deposit = response.json()
    assert deposit["payer_email"] == "sam@example.com"
    assert client.post("/admin/deposits", json=new).status_code == 409  # already in UnitRes

    reservation_id = reserve(units[0], "sam@example.com").json()["id"]
    in_use = client.post(f"/admin/deposits/{deposit['id']}/refunded")
    assert in_use.status_code == 409
    assert "Cancel that reservation first" in in_use.json()["detail"]

    client.post(f"/admin/reservations/{reservation_id}/cancel")
    refunded = client.post(f"/admin/deposits/{deposit['id']}/refunded")
    assert refunded.status_code == 200
    assert refunded.json()["refunded_at"] is not None

    assert eligibility("sam@example.com")["reason"] == "no_deposit"
    assert reserve(units[1], "sam@example.com").status_code == 402
    assert client.post(f"/admin/deposits/{deposit['id']}/refunded").status_code == 409


def test_staff_see_which_reservation_a_deposit_pays_for(units):
    pay_deposit("sam@example.com")
    reservation_id = reserve(units[0], "sam@example.com").json()["id"]

    [deposit] = client.get("/admin/deposits").json()
    assert deposit["active_reservation_id"] == reservation_id
    assert client.get("/admin/deposits", params={"unused": True}).json() == []
    [reservation] = client.get("/admin/reservations").json()
    assert reservation["deposit"]["id"] == deposit["id"]


def test_syncing_twice_saves_each_deposit_once():
    fake_entrata.add_payment("sam@example.com")
    fake_entrata.add_payment("sam@example.com", kind="application_fee")

    first = sync_once(fake_entrata)
    second = sync_once(fake_entrata)

    assert (first.new_deposits, first.already_seen, first.not_deposits) == (1, 0, 1)
    assert (second.new_deposits, second.already_seen, second.not_deposits) == (0, 1, 1)
    with SessionLocal() as db:
        assert db.query(Deposit).count() == 1


def test_seed_lets_you_try_reserve_right_away():
    seed()
    available = client.get("/apartments").json()
    assert len(available) == 4

    assert eligibility(PAID_STUDENT_EMAIL)["can_reserve"] is True
    assert reserve(available[0]["id"], PAID_STUDENT_EMAIL).status_code == 201
    assert len(client.get("/apartments").json()) == 3


def test_staff_delete_only_cancelled_reservations(units):
    pay_deposit("sam@example.com")
    reservation_id = reserve(units[0], "sam@example.com").json()["id"]

    # Confirmed: it's the student's unit, so staff have to cancel it first
    assert client.delete(f"/admin/reservations/{reservation_id}").status_code == 409

    client.post(f"/admin/reservations/{reservation_id}/cancel")
    assert client.delete(f"/admin/reservations/{reservation_id}").status_code == 204
    assert client.delete(f"/admin/reservations/{reservation_id}").status_code == 404

    # With the reservation gone, the apartment can be removed
    assert client.delete(f"/admin/apartments/{units[0]}").status_code == 204
