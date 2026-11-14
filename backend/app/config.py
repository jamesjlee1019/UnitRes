"""Settings, read from environment variables.

Inside Docker these come from docker-compose.yml and your .env file
(copy .env.example to .env to get started). Use them like this:

    from app.config import settings
    settings.entrata_mode
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]

JSM_APPLICATION_URL = (
    "https://entratasnippet2.jsmliving.com/Apartments/module/application_authentication/"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    # Docker sets this for you. The default is for running the API outside Docker.
    database_url: str = "postgresql+psycopg://unitres:unitres@localhost:5433/unitres"

    # Where the website runs
    frontend_url: str = "http://localhost:3000"

    # Payments: the Entrata handoff. Students pay the security deposit there first,
    # and Reserve only works once their deposit has shown up here.
    #   fake = a pretend Entrata inside the API, for development. Simulate deposits
    #          with POST /dev/entrata/payments.
    #   live = JSM's real Entrata, read-only. Needs the three ENTRATA_* keys below.
    entrata_mode: Literal["fake", "live"] = "fake"
    # Where a student who hasn't paid yet goes to apply and pay
    entrata_application_url: str = JSM_APPLICATION_URL
    # How often the API checks Entrata for new deposits, in seconds. 0 turns it off.
    # This is also about how long a student waits after paying before Reserve works.
    entrata_poll_seconds: int = 120
    # How far back each check looks. Payments already seen are skipped.
    entrata_lookback_days: int = 14
    # Live mode only, from JSM's Entrata internal API user
    entrata_subdomain: str = ""  # "jsmliving" for jsmliving.entrata.com
    entrata_api_key: str = ""
    entrata_deposit_charge_code: str = ""  # how JSM's Entrata labels a security deposit

    # Accounts: SendGrid key, the verified sender address, and the scheduling link
    sendgrid_api_key: str = ""
    from_email: str = ""
    calendly_url: str = ""


settings = Settings()
