"""Settings, read from environment variables.

Inside Docker these come from docker-compose.yml and your .env file
(copy .env.example to .env to get started). Use them like this:

    from app.config import settings
    settings.stripe_secret_key
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    # Docker sets this for you. The default is for running the API outside Docker.
    database_url: str = "postgresql+psycopg://unitres:unitres@localhost:5433/unitres"

    # Where the website runs. Payments uses it for Stripe's success and cancel links.
    frontend_url: str = "http://localhost:3000"

    # Payments: your Stripe test-mode secret key (starts with sk_test_)
    stripe_secret_key: str = ""

    # Accounts: SendGrid key, the verified sender address, and the scheduling link
    sendgrid_api_key: str = ""
    from_email: str = ""
    calendly_url: str = ""


settings = Settings()
