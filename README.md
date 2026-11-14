# JSM UnitRes

A website where students reserve an apartment at JSM Living.

## How reserving works

Students don't pay on our site. They apply and pay their security deposit through JSM's normal application, which runs on Entrata, the system JSM already uses. Once their deposit shows up on our end, they can reserve a unit here, and it's theirs right away.

1. The student applies and pays the deposit on JSM's site.
2. They come back to UnitRes and pick a unit.
3. That's it. The unit disappears from the list for everyone else.

One deposit gets you one unit, and two people can never reserve the same one.

## Getting it running

You need [Git](https://git-scm.com/downloads) and [Docker Desktop](https://www.docker.com/products/docker-desktop/). Open Docker once so it's running, then:

```bash
git clone https://github.com/jamesjlee1019/UnitRes.git
cd UnitRes
docker compose up
```

The first time takes a few minutes while everything installs. When the log says `Uvicorn running on http://0.0.0.0:8000` and `Local: http://localhost:3000/`, open [localhost:3000](http://localhost:3000). Three check marks means you're all set.

Press `Ctrl+C` to stop. After the first time, it starts in seconds.

## Trying it without real money

While we're building, the app talks to a pretend version of Entrata, so nobody pays anything. The sample data comes with five apartments (four open, one already taken) and one student who has already paid: `paid.student@example.com`.

To try it, open [localhost:8000/docs](http://localhost:8000/docs):

- **Reserve a unit:** use `POST /reservations` with `paid.student@example.com`.
- **Pretend someone new paid:** use `POST /dev/entrata/payments` with any email. That email can then reserve.

## Who works on what

| Team | What you own | Where your code lives |
| --- | --- | --- |
| Booking | The apartments list and the Reserve button | `backend/app/routers/booking.py`<br>`frontend/src/pages/ApartmentsPage.tsx` |
| Payments | Getting deposits in from Entrata | `backend/app/routers/payments.py`<br>`backend/app/entrata/` |
| Admin | The staff page | `backend/app/routers/admin.py`<br>`frontend/src/pages/AdminPage.tsx` |
| Accounts | Logins and emails | `backend/scripts/` |

Every file has a comment at the top saying what it's for. The site has three parts that talk to each other: the pages in `frontend/` (localhost:3000), the API in `backend/` (localhost:8000), and a PostgreSQL database.

## Handy commands

`docker compose up` keeps its terminal busy, so open a second one for these.

| To do this | Run this |
| --- | --- |
| See the API's errors | `docker compose logs -f api` |
| Run the tests | `docker compose exec api pytest` |
| Look inside the database | `docker compose exec db psql -U unitres` |
| Start over with fresh sample data | `docker compose down -v`, then `docker compose up` |

When you save a file, the site reloads on its own.

## Keys

Only Accounts needs keys right now, for sending email. Copy the example file and fill in your lines:

```bash
cp .env.example .env
```

Then restart with `Ctrl+C` and `docker compose up`. Git ignores `.env`, so your keys stay on your laptop. Please don't paste them in the group chat.

## Changing the database

If you add or change a table, edit `backend/app/models.py`, then make a migration so everyone else's database gets the same change:

```bash
docker compose exec api alembic revision --autogenerate -m "add accounts table"
```

Look over the new file in `backend/alembic/versions/`, then restart. Give the group chat a heads-up first: if two people add migrations at the same time, `docker compose up` breaks for everyone until one of them is fixed.

## Getting your work in

```bash
git checkout main && git pull
git checkout -b booking/apartment-list    # your team / what you're doing
# make your changes, then:
git add -A && git commit -m "Show available apartments"
git push -u origin booking/apartment-list
```

Then open a pull request on GitHub and have a teammate look it over before you merge. Small pull requests are easier to review, so merge often.
