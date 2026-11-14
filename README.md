# JSM UnitRes

A website where students reserve an apartment by paying an application fee.

Students see the open units, reserve one, pay, and get a "you're reserved" email with a link
to schedule their lease signing. Staff get a back-office page to add and remove units and see
who reserved what.

## Where things stand

Version 1 is done when all of these work on `main`:

- [x] The apartments page lists the available units from the database
- [x] The staff page adds apartments, removes them or marks them unavailable, and lists every reservation
- [ ] A student can reserve a unit and pay for it
- [ ] A reserved unit drops off the list, and the database refuses a second reservation for it, even if two people reserve at the same moment
- [ ] The "you're reserved" email goes out on its own after a reservation (for now, a test script sends it)

Open pull requests show what's in progress. When your PR finishes one of these, tick its box in the same PR.

## Run it on your laptop

You need [Git](https://git-scm.com/downloads) and [Docker Desktop](https://www.docker.com/products/docker-desktop/).
Open Docker once so it's running, then:

```bash
git clone https://github.com/jamesjlee1019/UnitRes.git
cd UnitRes
docker compose up
```

The first run takes a few minutes while everything installs. It's ready when the log says
`Uvicorn running on http://0.0.0.0:8000` and `Local: http://localhost:3000/`.
Open [localhost:3000](http://localhost:3000). Three check marks means it's working.

Press `Ctrl+C` to stop. After the first time, `docker compose up` starts in seconds.

| Open this | To see |
| --- | --- |
| [localhost:3000](http://localhost:3000) | The setup check |
| [localhost:3000/apartments](http://localhost:3000/apartments) | The available apartments |
| [localhost:3000/checkout](http://localhost:3000/checkout) | Paying the fee (not built yet) |
| [localhost:3000/admin](http://localhost:3000/admin) | The staff page |
| [localhost:8000/docs](http://localhost:8000/docs) | Every API endpoint, and you can try each one |

### Sample data

Your database starts with five apartments. Four are available, and one (B-215) is already
reserved by a test student. So the apartments page should show four, and the staff page
should show one reservation.

To start over with fresh sample data, run `docker compose down -v`, then `docker compose up`.

## Teams

Each team owns one feature, from the database all the way to the page.

| Team | What you own | Where your code lives |
| --- | --- | --- |
| Booking | The apartment list, reserving a unit, and making sure two people can't get the same one | `backend/app/routers/booking.py`<br>`frontend/src/pages/ApartmentsPage.tsx` |
| Payments | Paying the fee, marking the reservation as paid, and receipts | `backend/app/routers/payments.py`<br>`frontend/src/pages/CheckoutPage.tsx`<br>`frontend/src/pages/CheckoutSuccessPage.tsx` |
| Admin | The staff page: apartments and reservations, and later staff-only access and a log of who changed what | `backend/app/routers/admin.py`<br>`frontend/src/pages/AdminPage.tsx` |
| Accounts & notifications | Signup and login, resident vs. staff roles, and every email | `backend/scripts/send_test_email.py` for now |

Unfinished code is marked with `TODO`, and an endpoint that isn't built yet answers with "Not built yet".

## The API

| Endpoint | What it does | Team |
| --- | --- | --- |
| `GET /apartments` | Lists the available apartments | Booking |
| `POST /reservations` | Reserves an apartment for a student (not built yet) | Booking |
| `POST /payments/checkout-session` | Starts paying the fee (not built yet) | Payments |
| `GET /admin/apartments` | Lists every apartment, including unavailable ones | Admin |
| `POST /admin/apartments` | Adds an apartment | Admin |
| `PATCH /admin/apartments/{id}` | Changes an apartment, like marking it unavailable | Admin |
| `DELETE /admin/apartments/{id}` | Removes an apartment, unless it has reservations | Admin |
| `GET /admin/reservations` | Lists every reservation | Admin |
| `GET /health` | Checks that the API and database are up (the setup check uses it) | |

Prices are stored in cents, so `72500` means $725.00.

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
PostgreSQL       db          The apartments and reservations tables.
```

```
backend/
  app/
    main.py          the API app, plus the /health route
    models.py        the database tables
    schemas.py       the JSON the API sends and receives
    routers/         one file per team: booking.py, payments.py, admin.py
    seed.py          the sample data everyone starts with
  alembic/versions/  database changes (migrations), applied on startup
  scripts/           one-off scripts, like the test email
  tests/             backend tests
frontend/src/
  pages/             one page per screen
  api.ts             api() for calling the backend, plus shared types
  teams.ts           the team cards on the home page
docker-compose.yml   what "docker compose up" starts
```

If you're new to the code, two files are good examples to copy from: the `/health` route in
`backend/app/main.py` (reading the database) and `frontend/src/pages/HomePage.tsx`
(loading data on a page).

## Everyday commands

Run these from the `UnitRes` folder. `docker compose up` keeps its terminal busy,
so open a second terminal for the rest.

| To do this | Run this |
| --- | --- |
| Start everything | `docker compose up` |
| Stop | `Ctrl+C` |
| See the API's errors | `docker compose logs -f api` |
| Run the backend tests | `docker compose exec api pytest` |
| Look inside the database with SQL | `docker compose exec db psql -U unitres` |
| Start over with fresh sample data | `docker compose down -v`, then `docker compose up` |

Saving a file reloads things on its own: the API restarts when you save a `.py` file,
and the page updates when you save a `.tsx` file.

## Keys

Payments and Accounts need API keys. Booking and Admin can skip this.

```bash
cp .env.example .env
```

Fill in your team's lines, then restart (`Ctrl+C`, then `docker compose up`).
Git ignores `.env`, so your keys stay on your laptop. Don't paste them in the group chat.

## Changing the database

The tables live in `backend/app/models.py`. If you change one, also make a migration so
everyone else's database gets the same change. Pull the newest `main` into your branch first,
then run:

```bash
docker compose exec api alembic revision --autogenerate -m "add accounts table"
```

Look over the new file in `backend/alembic/versions/`, then restart. Migrations run on their
own when the API starts.

Give the group chat a heads-up before you merge one. If two migrations get merged on top of the
same one, startup fails with an error about "multiple head revisions". To fix it, point the
newer file's `down_revision` at the other one.

## Getting your work in

```bash
git checkout main && git pull
git checkout -b booking/apartment-list     # your team / what you're doing
# make your changes, then:
git add -A && git commit -m "Show available apartments"
git push -u origin booking/apartment-list
```

Then open a pull request into `main` on GitHub and have a teammate look it over before merging.
Keep pull requests small and merge often. Something counts as done once it works on `main`.
