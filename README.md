# JSM UnitRes

A website where students reserve an apartment at JSM Living.

Students pay their security deposit through JSM's normal application, then come here, pick an
open unit, and it's theirs right away. They get a "you're reserved" email with a link to
schedule their lease signing. Staff get a back-office page to add and remove units and see
who reserved what.

## How reserving works

Students don't pay on our site. They apply and pay their security deposit through JSM's normal
application, which runs on Entrata, the system JSM already uses. Once their deposit shows up on
our end, they can reserve a unit here.

1. The student applies and pays the deposit on JSM's site.
2. They come back to UnitRes and pick a unit.
3. That's it. The unit disappears from the list for everyone else.

One deposit gets you one unit, and two people can never reserve the same one.



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
| [localhost:3000/apartments](http://localhost:3000/apartments) | The available apartments, and reserving one |
| [localhost:3000/admin](http://localhost:3000/admin) | The staff page |
| [localhost:8000/docs](http://localhost:8000/docs) | Every API endpoint, and you can try each one |

The `/checkout` page is left over from the Stripe plan and isn't used anymore.

### Sample data

Your database starts with five apartments. Four are available, and one (B-215) is already
reserved by a test student. So the apartments page should show four, and the staff page
should show one reservation.

There's also one student who has already paid a deposit, `paid.student@example.com`, so you
can try reserving right away.

To start over with fresh sample data, run `docker compose down -v`, then `docker compose up`.

### Trying it without real money

While we're building, the app talks to a pretend version of Entrata, so nobody pays anything.

- **Reserve a unit:** on [localhost:3000/apartments](http://localhost:3000/apartments), enter `paid.student@example.com` and press Check my deposit.
- **Pretend someone new paid:** at [localhost:8000/docs](http://localhost:8000/docs), use `POST /dev/entrata/payments` with any email. That email can then reserve.
- **Get the email:** put the SendGrid lines in `.env` (see Keys) and reserve with an inbox you can check.

## Teams

Each team owns one feature, from the database all the way to the page.

| Team | What you own | Where your code lives |
| --- | --- | --- |
| Booking | The apartment list, the Reserve button, and making sure two people can't get the same unit | `backend/app/routers/booking.py`<br>`frontend/src/pages/ApartmentsPage.tsx` |
| Payments | Getting deposits in from Entrata | `backend/app/routers/payments.py`<br>`backend/app/entrata/` |
| Admin | The staff page: apartments and reservations, and later staff-only access and a log of who changed what | `backend/app/routers/admin.py`<br>`frontend/src/pages/AdminPage.tsx` |
| Accounts & notifications | Signup and login, resident vs. staff roles, and every email | `backend/app/notifications.py`<br>`backend/scripts/send_test_email.py` |

Unfinished code is marked with `TODO`.

## The API

| Endpoint | What it does | Team |
| --- | --- | --- |
| `GET /apartments` | Lists the apartments a student can reserve right now | Booking |
| `GET /eligibility?email=...` | Says whether this student has paid, so Reserve should be on | Booking |
| `POST /reservations` | Reserves a unit with the student's deposit. It's confirmed right away | Booking |
| `GET /admin/deposits` | Lists every deposit. `?unused=true` for ones not reserving anything | Payments |
| `POST /admin/deposits` | Adds a deposit staff can see in Entrata, by hand | Payments |
| `POST /admin/deposits/{id}/refunded` | Marks a deposit refunded, so it can't reserve anymore | Payments |
| `POST /admin/entrata/sync` | Checks Entrata for new deposits now, instead of waiting | Payments |
| `GET /admin/apartments` | Lists every apartment, including unavailable ones | Admin |
| `POST /admin/apartments` | Adds an apartment | Admin |
| `PATCH /admin/apartments/{id}` | Changes an apartment, like marking it unavailable | Admin |
| `DELETE /admin/apartments/{id}` | Removes an apartment, unless it has reservations | Admin |
| `GET /admin/reservations` | Lists every reservation | Admin |
| `POST /admin/reservations/{id}/cancel` | Cancels a reservation. The unit goes back on the list | Admin |
| `DELETE /admin/reservations/{id}` | Deletes a cancelled reservation | Admin |
| `POST /admin/reservations/{id}/entrata-updated` | Records that staff made Entrata match this reservation | Admin |
| `POST /dev/entrata/payments` | Pretends a student paid in Entrata (only with the pretend Entrata) | |
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
PostgreSQL       db          The apartments, reservations, deposits and accounts tables.
```

```
backend/
  app/
    main.py          the API app, plus the /health route
    models.py        the database tables
    schemas.py       the JSON the API sends and receives
    routers/         one file per team: booking.py, payments.py, admin.py (and dev.py for the pretend Entrata)
    entrata/         reading deposits from Entrata, and the pretend version
    reservations.py  reservation rules more than one team needs
    events.py        "reservation confirmed" and "cancelled", for emails to listen to
    notifications.py the emails
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

Only Accounts needs keys right now, for sending email. Payments can leave `ENTRATA_MODE=fake`
until we have keys from JSM. Booking and Admin can skip this.

```bash
cp .env.example .env
```

Fill in your team's lines, then restart (`Ctrl+C`, then `docker compose up`).
Git ignores `.env`, so your keys stay on your laptop. Don't paste them in the group chat.

With `SENDGRID_API_KEY` and `FROM_EMAIL` set, every confirmed reservation emails the student
"you're reserved" with the Calendly link. That's the only email the app sends. Without the keys,
reserving still works and `docker compose logs api` says the email was skipped.

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

## Getting the newest main

Do this before a demo, or before starting something new, so you're running what everyone has
merged. The commands are the same in PowerShell and in a Mac or Linux terminal.

**1. Check for changes you haven't committed.**

```bash
git status
```

If it says `nothing to commit, working tree clean`, skip to step 2. If it lists files, decide
whether you want to keep them.

To keep them, set them aside. `-u` includes new files too.

```bash
git stash push -u -m "what I was working on"
```

When you want them back, go to your branch and run `git stash pop`. If `main` changed the same
lines, git marks the conflicts in those files for you to fix.

To throw them away instead (this can't be undone):

```bash
git restore .
git clean -nd    # lists the new files it would delete
git clean -fd    # deletes them
```

`git clean` never touches `.env`, because git ignores that file.

**2. Switch to main and pull.**

```bash
git checkout main
git pull
git log -1 --oneline
```

The last line shows the newest commit you have. It should match the top of the
[commits on GitHub](https://github.com/jamesjlee1019/UnitRes/commits/main).

**3. Restart, so new packages and database changes get picked up.** If it's running, stop it
with `Ctrl+C` first.

```bash
docker compose down -v    # optional: also resets your database to the sample data
docker compose up
```

Leave out `docker compose down -v` if you want to keep the apartments and reservations you've added.

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
