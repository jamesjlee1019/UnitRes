"""ACCOUNTS TEAM, week 1: send the "you're reserved" email to your own inbox.

Run it from the repo root while the project is running:

    docker compose exec api python scripts/send_test_email.py you@stanford.edu

Setup: put SENDGRID_API_KEY, FROM_EMAIL and CALENDLY_URL in .env (README, "Keys"),
then restart. FROM_EMAIL has to be a sender you've verified in SendGrid.
SendGrid's Python guide: https://www.twilio.com/docs/sendgrid/for-developers/sending-email/quickstart-python
"""

import sys

from app.config import settings


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/send_test_email.py you@stanford.edu")
    to_email = sys.argv[1]

    subject = "You're reserved!"
    body = (
        "Your apartment is reserved.\n\n"
        f"Pick a time to sign your lease: {settings.calendly_url}\n"
    )

    # TODO (Accounts, week 1): send `subject` and `body` from settings.from_email
    # to `to_email` with SendGrid, using settings.sendgrid_api_key.
    # Week 2: move the sending into a function the rest of the app can use.
    print("Not built yet. Accounts team: see backend/scripts/send_test_email.py")
    print(f"\nThis would go to {to_email}:\n\nSubject: {subject}\n\n{body}")


if __name__ == "__main__":
    main()
