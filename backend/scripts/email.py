import sys
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import settings

def send_reservation_confirmation(to_email) -> None:
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


if __name__ == "__main__":
    to_email = sys.argv[1]
    send_reservation_confirmation(to_email)