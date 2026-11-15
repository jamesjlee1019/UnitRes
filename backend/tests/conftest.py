"""Shared test setup. pytest loads this file before any test.

Tests run against their own database, "<your database>_test", so running them never
touches the apartments you've been clicking around with. It's created and migrated
automatically, and emptied before each test.
"""

import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

# These must be set before anything imports app.config
_dev_url = make_url(
    os.environ.get("DATABASE_URL", "postgresql+psycopg://unitres:unitres@localhost:5433/unitres")
)
_test_url = _dev_url.set(database=f"{_dev_url.database}_test")
os.environ["DATABASE_URL"] = _test_url.render_as_string(hide_password=False)
os.environ["ENTRATA_MODE"] = "fake"
os.environ["ENTRATA_POLL_SECONDS"] = "0"  # tests run the sync themselves
os.environ["SENDGRID_API_KEY"] = ""  # never send real email from tests, even with keys in .env


def _create_test_database() -> None:
    admin = create_engine(_dev_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": _test_url.database}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{_test_url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session", autouse=True)
def test_database():
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    _create_test_database()
    command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")
    yield


@pytest.fixture(autouse=True)
def empty_tables(test_database):
    from app.db import engine
    from app.entrata.client import fake_entrata

    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE reservations, deposits, apartments RESTART IDENTITY CASCADE")
        )
    fake_entrata.clear()
    yield
