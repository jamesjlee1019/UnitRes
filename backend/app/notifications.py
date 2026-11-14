"""Emails the app sends, through SendGrid.

The "you're reserved" email goes out on its own: email_reservation_confirmed below
listens for the reservation_confirmed event (app/events.py), which Booking fires
right after a reservation is saved.

Anything else in the app can send one too:

    from app.notifications import send_reservation_confirmation
    send_reservation_confirmation("student@stanford.edu")

To try it from the command line, use scripts/send_test_email.py.

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
    """Send the "you're reserved" email. Returns True if SendGrid accepted it."""
    if not settings.sendgrid_api_key or not settings.from_email:
        log.warning(
            "Not emailing %s: SENDGRID_API_KEY or FROM_EMAIL is missing from .env", to_email
        )
        return False

    greeting = f"Hi {student_name},\n\n" if student_name else ""
    what = f"{unit} is reserved for you." if unit else "Your apartment is reserved."
    subject = "You're reserved!"
    body = (
        f"{greeting}{what}\n\n"
        f"Pick a time to sign your lease: {settings.calendly_url}\n\n"
        "JSM UnitRes\n"
    )

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    mail = Mail(Email(settings.from_email), To(to_email), subject, Content("text/plain", body))
    response = sg.client.mail.send.post(request_body=mail.get())
    log.info("Emailed %s, SendGrid answered %s", to_email, response.status_code)
    return 200 <= response.status_code < 300


def _in_background(work: Callable[[], None]) -> None:
    """Run it in its own thread, so the student doesn't wait on SendGrid to see their unit."""

    def run() -> None:
        try:
            work()
        except Exception:
            log.exception("Sending an email failed")

    threading.Thread(target=run, name="email", daemon=True).start()


@events.on("reservation_confirmed")
def email_reservation_confirmed(reservation_id: int) -> None:
    with SessionLocal() as db:
        reservation = db.get(Reservation, reservation_id)
        if reservation is None:
            return
        to_email = reservation.student_email
        name = reservation.student_name
        unit = f"{reservation.apartment.building}, unit {reservation.apartment.number}"

    _in_background(lambda: send_reservation_confirmation(to_email, name, unit))
