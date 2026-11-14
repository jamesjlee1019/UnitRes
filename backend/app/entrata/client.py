"""Reading payments from Entrata, JSM's property management system.

UnitRes never takes money. Students apply and pay in JSM's own Entrata application;
this module only reads what they paid, so the sync job can save their deposit and
let them reserve.

Two versions behind one interface:

    get_client().payments_since(some_datetime)  ->  list[EntrataPayment]

- FakeEntrata (ENTRATA_MODE=fake, the default): a pretend Entrata that lives inside
  the API. Nothing leaves your laptop, and no one pays a real $20.
- LiveEntrata (ENTRATA_MODE=live): JSM's real Entrata, read-only. Not written yet,
  because it needs JSM's API key to see what their data looks like. See its docstring.
"""

import itertools
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from app.config import settings
from app.reservations import utcnow

PaymentKind = Literal["security_deposit", "application_fee", "other"]

# Typical amounts for the fake, in cents. The $20 fee is from jsmliving.com.
FAKE_AMOUNTS: dict[PaymentKind, int] = {
    "security_deposit": 50_000,
    "application_fee": 2_000,
    "other": 10_000,
}


@dataclass(frozen=True)
class EntrataPayment:
    entrata_id: str  # Entrata's ID for the payment, unique
    payer_email: str
    amount_cents: int
    paid_at: datetime
    kind: PaymentKind  # only security deposits let a student reserve


class EntrataClient(Protocol):
    def payments_since(self, since: datetime) -> list[EntrataPayment]: ...


class FakeEntrata:
    """Pretend Entrata for development and tests.

    Payments live in memory, so they disappear when the API reloads. That's fine:
    the sync job copies deposits into the deposits table as soon as it sees them.
    """

    def __init__(self) -> None:
        self._payments: list[EntrataPayment] = []
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def add_payment(
        self,
        email: str,
        kind: PaymentKind = "security_deposit",
        amount_cents: int | None = None,
        paid_at: datetime | None = None,
    ) -> EntrataPayment:
        with self._lock:
            payment = EntrataPayment(
                entrata_id=f"FAKE-{next(self._ids):05d}",
                payer_email=email,
                amount_cents=amount_cents or FAKE_AMOUNTS[kind],
                paid_at=paid_at or utcnow(),
                kind=kind,
            )
            self._payments.append(payment)
            return payment

    def payments_since(self, since: datetime) -> list[EntrataPayment]:
        with self._lock:
            return [p for p in self._payments if p.paid_at >= since]

    def all_payments(self) -> list[EntrataPayment]:
        with self._lock:
            return list(self._payments)

    def clear(self) -> None:
        with self._lock:
            self._payments.clear()
            self._ids = itertools.count(1)


class LiveEntrata:
    """JSM's real Entrata, read-only. TODO (Payments), once JSM's API key arrives.

    JSM requests an internal API user from their Entrata customer success manager.
    Ask for read-only access. It goes in .env as ENTRATA_SUBDOMAIN and ENTRATA_API_KEY.

    What to build in payments_since():
      1. Call Entrata's AR payments method (getArPayments, at
         https://<subdomain>.entrata.com/api/v1/arpayments) for payments since `since`.
         The request format and auth header are in Entrata's docs, at
         docs.entrata.com/api/v1/documentation once you're signed in.
         Entrata's API is POST-only, even for reads.
      2. Turn each one into an EntrataPayment. Set kind="security_deposit" only when its
         charge code matches ENTRATA_DEPOSIT_CHARGE_CODE (ask JSM what they call it).
         Everything else, including the $20 application fee, is "application_fee" or "other".
      3. If a payment doesn't include the payer's email, look it up from their
         customer record (getCustomers) before returning it. Students reserve with that email.

    Test it against a few real payments with JSM before turning on ENTRATA_MODE=live.
    Nothing here ever writes to Entrata.
    """

    def __init__(self, subdomain: str, api_key: str, deposit_charge_code: str) -> None:
        missing = [
            name
            for name, value in [
                ("ENTRATA_SUBDOMAIN", subdomain),
                ("ENTRATA_API_KEY", api_key),
                ("ENTRATA_DEPOSIT_CHARGE_CODE", deposit_charge_code),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(f"ENTRATA_MODE=live needs {', '.join(missing)} in .env")
        self.subdomain = subdomain
        self.api_key = api_key
        self.deposit_charge_code = deposit_charge_code

    def payments_since(self, since: datetime) -> list[EntrataPayment]:
        raise NotImplementedError(
            "Live Entrata isn't built yet (see LiveEntrata in backend/app/entrata/client.py). "
            "Use ENTRATA_MODE=fake, or add deposits by hand with POST /admin/deposits."
        )


# One shared fake, so the dev endpoints and the sync job see the same payments
fake_entrata = FakeEntrata()


def get_client() -> EntrataClient:
    if settings.entrata_mode == "fake":
        return fake_entrata
    return LiveEntrata(
        settings.entrata_subdomain, settings.entrata_api_key, settings.entrata_deposit_charge_code
    )
