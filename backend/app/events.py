"""Events other teams fire, and the Accounts team listens to (kickoff slide 7).

Firing, from any team's code, after the database change is committed:

    from app import events
    events.fire("reservation_confirmed", reservation_id)

Listening, in the Accounts team's code:

    @events.on("reservation_confirmed")
    def send_youre_reserved_email(reservation_id: int) -> None:
        ...

This is the simplest version: listeners run right away, in the same process.
How emails go out in the background, and what happens when a send fails, is
the Accounts team's hard question, so they may well replace the inside of fire().
Keep the two function names and nobody else has to change anything.
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Literal

log = logging.getLogger("unitres.events")

EventName = Literal["reservation_confirmed", "reservation_cancelled"]
Listener = Callable[[int], None]

_listeners: dict[str, list[Listener]] = defaultdict(list)


def on(event: EventName) -> Callable[[Listener], Listener]:
    """Decorator: run this function whenever `event` fires."""

    def register(listener: Listener) -> Listener:
        _listeners[event].append(listener)
        return listener

    return register


def fire(event: EventName, reservation_id: int) -> None:
    """Tell the listeners. A listener that crashes is logged, never raised,
    so a failed email can't undo a reservation that's already confirmed."""
    log.info("event %s reservation_id=%s", event, reservation_id)
    for listener in _listeners[event]:
        try:
            listener(reservation_id)
        except Exception:
            log.exception("listener %s failed for %s", listener.__name__, event)
