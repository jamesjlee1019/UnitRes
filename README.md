# JSM UnitRes

A website where students reserve an apartment by paying an application fee.

## Set up (once)

1. **Install two things**
   - [Git](https://git-scm.com/downloads)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/). Open it once so it's running.

   On Windows, clone and work inside WSL (the Ubuntu terminal), not in a `C:\` folder.
   It's much faster there.

2. **Get the code**

   ```bash
   git clone https://github.com/jamesjlee1019/UnitRes.git
   cd UnitRes
   ```

3. **Start it**

   ```bash
   docker compose up
   ```

   The first run downloads and installs everything, so give it a few minutes.
   It's ready when the log says `Uvicorn running on http://0.0.0.0:8000` and `Local: http://localhost:3000/`.

4. **Open [localhost:3000](http://localhost:3000)**. Three check marks means you're set up.

To stop, press `Ctrl+C`. Next time, `docker compose up` starts in seconds.

## Week 1, by team

| Team | Goal | Your code goes in |
| --- | --- | --- |
| Booking | The apartments page shows the available units from the database | `backend/app/routers/booking.py`<br>`frontend/src/pages/ApartmentsPage.tsx` |
| Payments | A button opens Stripe Checkout in test mode, and card 4242 goes through to a success page | `backend/app/routers/payments.py`<br>`frontend/src/pages/CheckoutPage.tsx`<br>`frontend/src/pages/CheckoutSuccessPage.tsx` |
| Admin | A form on the staff page adds an apartment to the database | `backend/app/routers/admin.py`<br>`frontend/src/pages/AdminPage.tsx` |
| Accounts | A script sends the "you're reserved" email, with the Calendly link, to your own inbox | `backend/scripts/send_test_email.py` |

Each of those files starts with a comment saying what to build, with `TODO` where the code goes.
Two files are working examples to copy from: the `/health` route in `backend/app/main.py`
(reading the database) and `frontend/src/pages/HomePage.tsx` (loading data on a page).

Also bring your team's written answer to its hard question from the kickoff.

## Everyday commands

Run these from the `UnitRes` folder. `docker compose up` keeps its terminal busy,
so open a second terminal for the rest.

| To do this | Run this |
| --- | --- |
| Start everything | `docker compose up` |
| Stop | `Ctrl+C` |
| See the API's errors | `docker compose logs -f api` |
| Try any API endpoint in your browser | open [localhost:8000/docs](http://localhost:8000/docs) |
| Run the backend tests | `docker compose exec api pytest` |
| Look inside the database with SQL | `docker compose exec db psql -U unitres` |
| Wipe your database and reload the sample data | `docker compose down -v`, then `docker compose up` |

Saving a file reloads things on its own: the API restarts when you save a `.py` file,
and the page updates when you save a `.tsx` file.

## How it fits together

```
your browser
   │
   ▼
localhost:3000   frontend/   React pages. fetch('/api/...') is forwarded to the API.
   │
   ▼
localhost:8000   backend/    FastAPI. Each team has a file in backend/app/routers/.
   │
   ▼
PostgreSQL       db          The apartments and reservations tables (kickoff slide 4).
```

```
backend/
  app/
    main.py          the API app, plus the /health example
    models.py        the database tables
    schemas.py       the JSON the API sends and receives
    routers/         one file per team: booking.py, payments.py, admin.py
    seed.py          the sample apartments everyone starts with
  alembic/versions/  schema changes (migrations), applied on startup
  scripts/           one-off scripts, like the Accounts test email
  tests/
frontend/src/
  pages/             one page per screen
  api.ts             api() for calling the backend, plus shared types
  teams.ts           each team's week-1 goal, shown on the home page
docker-compose.yml   what "docker compose up" starts
```

The sample data has five apartments. Four are available (the units from the kickoff mock)
and one is already reserved, so a correct apartments page shows four.

## Keys (Payments and Accounts)

Booking and Admin can skip this. Payments and Accounts need API keys in a `.env` file:

```bash
cp .env.example .env
```

Fill in your team's lines, then stop (`Ctrl+C`) and run `docker compose up` again.
`.env` is ignored by Git, so keys stay on your laptop. Don't post them in the group chat.

- **Payments:** make a free Stripe account. Test mode works right away, with no business details
  needed. Your test secret key starts with `sk_test_` and is at
  [dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys).
- **Accounts:** ask James for the SendGrid key and the verified sender address.
  SendGrid's free trial lasts 60 days, so the team shares one account and starts it only when ready to send.

## Git: how to get your work in

```bash
git checkout main && git pull
git checkout -b booking/apartment-list     # team name / what you're doing
# ...make changes, then:
git add -A && git commit -m "Show available apartments"
git push -u origin booking/apartment-list
```

Then open a pull request into `main` on GitHub and have a teammate look it over before merging.
Keep pull requests small and merge often. A goal counts as done once it works on `main`.

## Changing the schema

Talk to James first, since every team reads these tables. Then:

1. Edit `backend/app/models.py`.
2. Generate a migration:
   `docker compose exec api alembic revision --autogenerate -m "add users table"`
3. Read the new file in `backend/alembic/versions/`. Autogenerate can miss things.
4. Restart. Everyone else's database picks up the change when they pull and run `docker compose up`.

## When something goes wrong

- **"Cannot connect to the Docker daemon"**: open Docker Desktop and wait for it to finish starting.
- **"port is already allocated"**: another program is using port 3000, 8000 or 5433. Quit it, or
  change the first number of that port in `docker-compose.yml`.
- **The setup check shows a ✕**: look at `docker compose logs -f api`. The last error is usually the answer.
- **Weird errors after pulling someone's changes**: run `docker compose up --build`.
- **Your database is in a strange state**: `docker compose down -v`, then `docker compose up`.
  This deletes your local data and reloads the sample apartments.
- **Your editor underlines every import in red**: the packages live inside Docker, so your editor can't
  see them. It doesn't affect running the project. To fix the underlines, run `npm install` in
  `frontend/` (needs [Node 24](https://nodejs.org/)), and for Python, make a virtual environment in
  `backend/` and `pip install -r requirements.txt`.
- **Still stuck after 20 minutes**: ask in the group chat, with the error message and what you ran.
