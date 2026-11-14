"""DEVELOPMENT ONLY: controls for the pretend Entrata.

Only exists when ENTRATA_MODE=fake (app/main.py checks), so it can never touch real money.
Lets the team test the whole flow without anyone paying a real deposit:

    1. POST /dev/entrata/payments with some email: "this student paid their deposit"
    2. The sync job runs right away and saves the deposit
    3. Reserve a unit on the website with that same email. It's confirmed immediately.

kind="application_fee" pretends they only paid the $20 fee, which shouldn't unlock Reserve.
"""

from dataclasses import asdict

from fastapi import APIRouter

from app.entrata.client import fake_entrata
from app.entrata.sync import sync_once
from app.schemas import FakeDepositIn

router = APIRouter(prefix="/dev/entrata", tags=["Development: fake Entrata"])


@router.post("/payments")
def simulate_payment(payment: FakeDepositIn):
    """Pretend this student paid in Entrata, then run the sync right away."""
    created = fake_entrata.add_payment(
        email=payment.email, kind=payment.kind, amount_cents=payment.amount_cents
    )
    summary = sync_once(fake_entrata)
    return {"payment": asdict(created), "sync": summary}


@router.get("/payments")
def list_fake_payments():
    """Everything paid in the pretend Entrata since the API last restarted."""
    return [asdict(p) for p in fake_entrata.all_payments()]
