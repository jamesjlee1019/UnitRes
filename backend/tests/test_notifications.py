"""The "you're reserved" email goes out only when a reservation is confirmed.

SendGrid is replaced with a fake here, so these never send real email.
Run from the repo root:  docker compose exec api pytest
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app import notifications
from app.config import settings
from app.db import SessionLocal
from app.main import app
from app.models import Apartment

client = TestClient(app)


class FakeSendGrid:
    """Stands in for sendgrid.SendGridAPIClient and remembers what it was asked to send."""

    sent: list[dict] = []
    fail = False

    def __init__(self, api_key: str):
        self.client = self

    @property
    def mail(self):
        return self

    @property
    def send(self):
        return self

    def post(self, request_body: dict):
        if FakeSendGrid.fail:
            raise RuntimeError("SendGrid is down")
        FakeSendGrid.sent.append(request_body)
        return type("Response", (), {"status_code": 202})()


@pytest.fixture
def sendgrid(monkeypatch) -> type[FakeSendGrid]:
    """Pretend SendGrid is set up, and record each email instead of sending it."""
    FakeSendGrid.sent = []
    FakeSendGrid.fail = False
    monkeypatch.setattr(notifications.sendgrid, "SendGridAPIClient", FakeSendGrid)
    monkeypatch.setattr(settings, "sendgrid_api_key", "SG.test")
    monkeypatch.setattr(settings, "from_email", "housing@example.com")
    monkeypatch.setattr(settings, "calendly_url", "https://calendly.com/jsm-test")
    # Send right away instead of in a thread, so the test can check it
    monkeypatch.setattr(notifications, "_in_background", lambda work: work())
    return FakeSendGrid


@pytest.fixture
def unit_id() -> int:
    with SessionLocal() as db:
        apartment = Apartment(number="A-101", building="Building A", bedrooms=1, price_cents=72_500)
        db.add(apartment)
        db.commit()
        return apartment.id


def reserve(unit_id: int, email: str = "sam@example.com"):
    return client.post(
        "/reservations",
        json={"apartment_id": unit_id, "student_name": "Sam Student", "student_email": email},
    )


def pay(email: str = "sam@example.com") -> None:
    client.post("/dev/entrata/payments", json={"email": email})


def test_reserving_emails_the_student(sendgrid, unit_id):
    pay()
    assert reserve(unit_id).status_code == 201

    assert len(sendgrid.sent) == 1
    email = sendgrid.sent[0]
    assert email["personalizations"][0]["to"][0]["email"] == "sam@example.com"
    assert email["subject"] == "You're reserved!"
    body = email["content"][0]["value"]
    assert "Hi Sam Student" in body
    assert "Unit A-101 in Building A is reserved for you." in body
    assert "https://calendly.com/jsm-test" in body


def test_no_deposit_or_already_reserved_sends_nothing(sendgrid, unit_id):
    # No deposit yet, so no reservation and no email
    assert reserve(unit_id).status_code == 402
    assert sendgrid.sent == []

    pay()
    assert reserve(unit_id).status_code == 201
    assert len(sendgrid.sent) == 1

    # Their deposit already reserved a unit, so no second email
    assert reserve(unit_id).status_code == 409
    assert len(sendgrid.sent) == 1


def test_reserving_works_without_email_keys(sendgrid, unit_id, monkeypatch):
    monkeypatch.setattr(settings, "sendgrid_api_key", "")
    pay()

    assert reserve(unit_id).status_code == 201
    assert sendgrid.sent == []


def test_sendgrid_being_down_does_not_undo_the_reservation(sendgrid, unit_id):
    sendgrid.fail = True
    pay()

    assert reserve(unit_id).status_code == 201
    assert unit_id not in {a["id"] for a in client.get("/apartments").json()}


def test_a_failed_background_send_is_logged_not_raised(caplog, monkeypatch):
    # The test database's migration loads alembic.ini's logging setup, which turns off
    # loggers that already exist. Turn this one back on so the test can read it.
    monkeypatch.setattr(notifications.log, "disabled", False)

    def sendgrid_down() -> None:
        raise RuntimeError("SendGrid is down")

    with caplog.at_level(logging.ERROR, logger="unitres.notifications"):
        thread = notifications._in_background(sendgrid_down)
        thread.join(timeout=5)

    assert not thread.is_alive()
    assert "Couldn't send an email" in caplog.text
