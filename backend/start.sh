#!/bin/sh
# What the api container runs when it starts.
set -e

# Install any packages someone added to requirements.txt since you last started
pip install --quiet --disable-pip-version-check --root-user-action=ignore -r requirements.txt

# Bring your database up to the latest schema (runs any new migrations)
alembic upgrade head

# Add the sample apartments if the database is empty
python -m app.seed

# Start the API. --reload restarts it whenever you save a .py file.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
