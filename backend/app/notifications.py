"""Emails the app sends, through SendGrid.

The "you're reserved" email goes out on its own whenever a reservation is confirmed:
email_when_reserved below listens for the reservation_confirmed event (app/events.py),
which Booking fires right after a reservation is saved. That's the only email for now.
A student who hasn't paid yet, or whose deposit already reserved a unit, just sees a
message on the page.

To try the email by hand, use scripts/send_test_email.py.

No SENDGRID_API_KEY or FROM_EMAIL in .env? Then nothing is sent, and the API log
says so. Reserving still works.
"""

import logging
import threading
from collections.abc import Callable

import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To

from app import events
from app.config import settings
from app.db import SessionLocal
from app.models import Reservation

log = logging.getLogger("unitres.notifications")


def send_reservation_confirmation(
    to_email: str, student_name: str | None = None, unit: str | None = None
) -> bool:
    """Send the "you're reserved" email, with the link to schedule a lease signing.
    Returns True if SendGrid accepted it."""
    if not settings.sendgrid_api_key or not settings.from_email:
        log.warning(
            "Not emailing %s: SENDGRID_API_KEY or FROM_EMAIL is missing from .env", to_email
        )
        return False

    greeting = f"Hi {student_name},\n\n" if student_name else ""
    reserved = f"{unit} is reserved for you." if unit else "Your apartment is reserved."
    subject = "You're reserved!"
    body = (
        f"{greeting}{reserved}\n\n"
        f"Pick a time to sign your lease: {settings.calendly_url}\n\n"
        "JSM UnitRes\n"
    )

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    mail = Mail(Email(settings.from_email), To(to_email), subject, Content("text/plain", body))
    response = sg.client.mail.send.post(request_body=mail.get())
    log.info("Sent the 'you're reserved' email to %s (SendGrid %s)", to_email, response.status_code)
    return 200 <= response.status_code < 300


def _in_background(work: Callable[[], object]) -> threading.Thread:
    """Run it in its own thread, so a slow or failing SendGrid never holds up reserving.
    The reservation is already confirmed either way."""

    def run() -> None:
        try:
            work()
        except Exception:
            log.exception("Couldn't send an email")

    thread = threading.Thread(target=run, name="email", daemon=True)
    thread.start()
    return thread


@events.on("reservation_confirmed")
def email_when_reserved(reservation_id: int) -> None:
    """A student just reserved a unit: email them. Nothing else triggers an email."""
    with SessionLocal() as db:
        reservation = db.get(Reservation, reservation_id)
        if reservation is None or reservation.status != "confirmed":
            return
        to_email = reservation.student_email
        name = reservation.student_name
        unit = f"Unit {reservation.apartment.number} in {reservation.apartment.building}"

    _in_background(lambda: send_reservation_confirmation(to_email, name, unit))
