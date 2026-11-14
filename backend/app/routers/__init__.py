"""One file per team: booking.py, payments.py, admin.py. dev.py is the fake Entrata."""

from fastapi import HTTPException


def not_built_yet(team: str, where: str) -> HTTPException:
    """What an endpoint returns until its team builds it (HTTP 501 = Not Implemented)."""
    return HTTPException(status_code=501, detail=f"Not built yet. {team} team: see {where}")
