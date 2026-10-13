"""PAYMENTS TEAM: Stripe Checkout for the application fee.

Week 1: the button at http://localhost:3000/checkout calls POST /payments/checkout-session,
the student pays on Stripe's page with test card 4242 4242 4242 4242, and Stripe sends
them back to http://localhost:3000/checkout/success. No database changes yet.

Setup: put your test-mode secret key in .env as STRIPE_SECRET_KEY (README, "Keys").
Stripe's guide (choose Python on the page): https://docs.stripe.com/checkout/quickstart
"""

import stripe  # noqa: F401  (you'll need this)
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.routers import not_built_yet

router = APIRouter(tags=["Payments"])

APPLICATION_FEE_CENTS = 5000  # $50.00, a placeholder until the real fee is decided


@router.post("/payments/checkout-session")
def create_checkout_session():
    """Start a Stripe Checkout and return the URL to send the student to."""
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=500,
            detail="STRIPE_SECRET_KEY is missing. Add it to .env (README, Keys), then restart.",
        )
    # TODO (Payments, week 1): create a Checkout Session in "payment" mode
    # for APPLICATION_FEE_CENTS, with
    #     success_url = f"{settings.frontend_url}/checkout/success"
    #     cancel_url  = f"{settings.frontend_url}/checkout"
    # and return {"url": session.url}. The /checkout page sends the student there.
    raise not_built_yet("Payments", "backend/app/routers/payments.py")
