"""ACCOUNTS TEAM, week 1: send the "you're reserved" email to your own inbox.

Run it from the repo root while the project is running:

    docker compose exec api python scripts/send_test_email.py you@stanford.edu

Setup: put SENDGRID_API_KEY, FROM_EMAIL and CALENDLY_URL in .env (README, "Keys"),
then restart. FROM_EMAIL has to be a sender you've verified in SendGrid.
SendGrid's Python guide: https://www.twilio.com/docs/sendgrid/for-developers/sending-email/quickstart-python

The email itself is built and sent in app/notifications.py.
"""

import sys

from app.notifications import send_reservation_confirmation


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/send_test_email.py you@stanford.edu")
    send_reservation_confirmation(sys.argv[1])


if __name__ == "__main__":
    main()
