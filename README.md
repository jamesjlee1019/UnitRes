# JSM UnitRes

A website where students reserve an apartment by paying an application fee.

## Set up (once)

1. **Install two things**
   - [Git](https://git-scm.com/downloads)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/). Open it once so it's running.


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
`.env` is ignored by Git, so keys stay on your laptop.


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

