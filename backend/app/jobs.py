"""Background work that runs inside the API process while it's up.

Right now that's one job: every ENTRATA_POLL_SECONDS, look for new security deposits
in Entrata. Set ENTRATA_POLL_SECONDS=0 to turn it off.
"""

import logging
import threading
from collections.abc import Callable

from app.entrata.sync import sync_once

log = logging.getLogger("unitres.jobs")


def start_entrata_sync(every_seconds: int) -> Callable[[], None]:
    """Start the loop in a background thread. Returns a function that stops it."""
    stop = threading.Event()

    def loop() -> None:
        while not stop.is_set():
            try:
                sync_once()
            except NotImplementedError as error:
                log.warning("Entrata sync skipped: %s", error)
            except Exception:
                # Entrata down, database restarting, ... Try again next time.
                log.exception("Entrata sync failed. Trying again in %s seconds.", every_seconds)
            stop.wait(every_seconds)

    thread = threading.Thread(target=loop, name="entrata-sync", daemon=True)
    thread.start()
    log.info("Entrata sync running every %s seconds", every_seconds)

    def stop_loop() -> None:
        stop.set()
        thread.join(timeout=5)

    return stop_loop
