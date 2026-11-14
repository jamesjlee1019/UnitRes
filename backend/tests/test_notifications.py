"""The "you're reserved" email goes out on its own after a reservation.

SendGrid is replaced with a fake here, so these never send real email.
"""

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


def pay_and_reserve(unit_id: int, email: str = "sam@example.com"):
    client.post("/dev/entrata/payments", json={"email": email})
    return client.post(
        "/reservations",
        json={"apartment_id": unit_id, "student_name": "Sam Student", "student_email": email},
    )


def test_reserving_emails_the_student(sendgrid, unit_id):
    assert pay_and_reserve(unit_id).status_code == 201

    assert len(sendgrid.sent) == 1
    email = sendgrid.sent[0]
    assert email["personalizations"][0]["to"][0]["email"] == "sam@example.com"
    assert email["subject"] == "You're reserved!"
    body = email["content"][0]["value"]
    assert "Building A, unit A-101" in body
    assert "https://calendly.com/jsm-test" in body


def test_no_email_when_reserve_fails(sendgrid, unit_id):
    # No deposit, so no reservation and no email
    response = client.post(
        "/reservations",
        json={"apartment_id": unit_id, "student_name": "Sam", "student_email": "sam@example.com"},
    )
    assert response.status_code == 402
    assert sendgrid.sent == []


def test_reserving_works_without_email_keys(sendgrid, unit_id, monkeypatch):
    monkeypatch.setattr(settings, "sendgrid_api_key", "")
    assert pay_and_reserve(unit_id).status_code == 201
    assert sendgrid.sent == []


def test_sendgrid_being_down_does_not_undo_the_reservation(sendgrid, unit_id):
    sendgrid.fail = True
    assert pay_and_reserve(unit_id).status_code == 201
    assert unit_id not in {a["id"] for a in client.get("/apartments").json()}
