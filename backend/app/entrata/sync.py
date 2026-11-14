"""The sync job: copies security deposits from Entrata into the deposits table.

It runs every ENTRATA_POLL_SECONDS in the background (see app/main.py), and staff can
run it on demand with POST /admin/entrata/sync. Running it twice is harmless:
each Entrata payment is saved once, by its Entrata ID.

It doesn't reserve anything. Once a student's deposit is in the table, Reserve works
for their email (app/routers/booking.py).
Only security deposits count. The $20 application fee is skipped.
"""

import logging
from datetime import timedelta

from sqlalchemy.dialects.postgresql import insert

from app.config import settings
from app.db import SessionLocal
from app.entrata.client import EntrataClient, get_client
from app.models import Deposit
from app.reservations import utcnow
from app.schemas import SyncSummary

log = logging.getLogger("unitres.entrata")


def sync_once(client: EntrataClient | None = None) -> SyncSummary:
    client = client or get_client()

    since = utcnow() - timedelta(days=settings.entrata_lookback_days)
    payments = client.payments_since(since)
    deposits = [p for p in payments if p.kind == "security_deposit"]
    summary = SyncSummary(
        new_deposits=0, already_seen=0, not_deposits=len(payments) - len(deposits)
    )

    with SessionLocal() as db:
        for payment in deposits:
            # If this payment is already saved, this does nothing and returns no id
            new_id = db.scalar(
                insert(Deposit)
                .values(
                    entrata_id=payment.entrata_id,
                    payer_email=payment.payer_email.strip().lower(),
                    amount_cents=payment.amount_cents,
                    paid_at=payment.paid_at,
                )
                .on_conflict_do_nothing(index_elements=["entrata_id"])
                .returning(Deposit.id)
            )
            if new_id is None:
                summary.already_seen += 1
            else:
                summary.new_deposits += 1
        db.commit()

    if summary.new_deposits:
        log.info("Entrata sync: %s", summary.model_dump())
    return summary
