"""ACCOUNTS TEAM, week 1: send the "you're reserved" email to your own inbox.

Run it from the repo root while the project is running:

    docker compose exec api python scripts/send_test_email.py you@stanford.edu

Setup: put SENDGRID_API_KEY, FROM_EMAIL and CALENDLY_URL in .env (README, "Keys"),
then restart. FROM_EMAIL has to be a sender you've verified in SendGrid.
SendGrid's Python guide: https://www.twilio.com/docs/sendgrid/for-developers/sending-email/quickstart-python
"""

import sys
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

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

    # Import API Key
    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    # Components of Email
    from_email = Email(settings.from_email)
    content = Content("text/plain", body)
    # Creates a Mail object from components of an email
    mail = Mail(from_email, To(to_email), subject, content)
    # Gets JSON representation of mail object
    mail_json = mail.get()
    # Sends HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)


    # print("Not built yet. Accounts team: see backend/scripts/send_test_email.py")
    # print(f"\nThis would go to {to_email}:\n\nSubject: {subject}\n\n{body}")


if __name__ == "__main__":
    main()
