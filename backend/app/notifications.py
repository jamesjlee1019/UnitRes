"""Emails the app sends, through SendGrid.

Anything in the app can send one:

    from app.notifications import send_reservation_confirmation
    send_reservation_confirmation("student@stanford.edu")

To try it from the command line, use scripts/send_test_email.py.
"""

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import settings


def send_reservation_confirmation(to_email: str) -> None:
    subject = "You're reserved!"
    body = (
        "Your apartment is reserved.\n\n"
        f"Pick a time to sign your lease: {settings.calendly_url}\n"
    )

    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    from_email = Email(settings.from_email)
    content = Content("text/plain", body)
    mail = Mail(from_email, To(to_email), subject, content)
    mail_json = mail.get()
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)
