import { useEffect, useState, type FormEvent } from 'react'
import {
  api,
  formatDollars,
  type Apartment,
  type Eligibility,
  type NewReservation,
  type StudentReservation,
} from '../api.ts'

/**
 * BOOKING TEAM: the list of available apartments, and reserving one.
 *
 * Students pay their security deposit in JSM's Entrata first. Here they type the
 * same email, we check it with GET /eligibility, and if their deposit has shown up
 * the Reserve buttons turn on. POST /reservations confirms it right away.
 *
 * When Accounts adds login, use the logged-in student's name and email instead of the form.
 */
export default function ApartmentsPage() {
  const [apartments, setApartments] = useState<Apartment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [checking, setChecking] = useState(false)
  const [eligibility, setEligibility] = useState<Eligibility | null>(null)
  const [checkError, setCheckError] = useState<string | null>(null)

  const [reservingId, setReservingId] = useState<number | null>(null)
  const [reserveError, setReserveError] = useState<string | null>(null)
  const [reserved, setReserved] = useState<StudentReservation | null>(null)

  function loadApartments() {
    return api<Apartment[]>('/apartments')
      .then((list) => {
        setApartments(list)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadApartments()
  }, [])

  async function checkDeposit(event: FormEvent) {
    event.preventDefault()
    setChecking(true)
    setCheckError(null)
    setReserveError(null)
    try {
      setEligibility(await api<Eligibility>(`/eligibility?email=${encodeURIComponent(email.trim())}`))
    } catch (err) {
      setEligibility(null)
      setCheckError((err as Error).message)
    } finally {
      setChecking(false)
    }
  }

  async function reserve(apartment: Apartment) {
    setReservingId(apartment.id)
    setReserveError(null)
    const body: NewReservation = {
      apartment_id: apartment.id,
      student_name: name.trim(),
      student_email: email.trim(),
    }
    try {
      const reservation = await api<StudentReservation>('/reservations', {
        method: 'POST',
        body: JSON.stringify(body),
      })
      setReserved(reservation)
      setEligibility((prev) =>
        prev && { ...prev, can_reserve: false, reason: 'already_reserved', reserved: reservation },
      )
    } catch (err) {
      // Most likely someone else just took it. The list below is refreshed either way.
      setReserveError((err as Error).message)
    } finally {
      setReservingId(null)
      loadApartments()
    }
  }

  const canReserve = eligibility?.can_reserve === true && name.trim() !== ''

  return (
    <section>
      <h1 className="text-4xl font-bold tracking-tight">Available apartments</h1>

      {reserved ? (
        <div className="mt-8 rounded-md border-2 border-ink bg-paper p-5">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">You're reserved</p>
          <h2 className="mt-2 text-2xl font-bold">
            {reserved.apartment.building}, unit {reserved.apartment.number}
          </h2>
          <p className="mt-2">
            It's yours. We sent a confirmation to <strong>{email.trim()}</strong> with a link to
            schedule your lease signing.
          </p>
        </div>
      ) : (
        <form
          onSubmit={checkDeposit}
          className="mt-8 grid max-w-xl gap-4 rounded-md border-2 border-ink bg-paper p-5"
        >
          <div>
            <h2 className="text-xl font-bold">Reserve a unit</h2>
            <p className="mt-1 text-sm text-muted">
              First apply and pay your security deposit on JSM's site. Then enter the same email
              here to turn on the Reserve buttons.
            </p>
          </div>
          <label className="block text-sm font-semibold">
            Your name
            <input
              className={INPUT}
              required
              maxLength={200}
              placeholder="Sam Student"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <label className="block text-sm font-semibold">
            Email on your JSM application
            <input
              className={INPUT}
              type="email"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setEligibility(null) // a different email has to be checked again
              }}
            />
          </label>
          <button
            type="submit"
            disabled={checking}
            className="justify-self-start rounded bg-brand px-4 py-2 font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {checking ? 'Checking…' : 'Check my deposit'}
          </button>

          {checkError && <p className="font-semibold text-brand">Couldn't check: {checkError}</p>}
          {eligibility?.reason === 'ok' && (
            <p className="font-semibold">Your deposit is in. Pick a unit below.</p>
          )}
          {eligibility?.reason === 'no_deposit' && (
            <p>
              We haven't seen a security deposit from {email.trim()} yet.{' '}
              <a
                href={eligibility.entrata_application_url}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-brand underline"
              >
                Apply and pay on JSM's site
              </a>
              , then check again. It can take a few minutes to show up here.
            </p>
          )}
          {eligibility?.reason === 'already_reserved' && eligibility.reserved && (
            <p className="font-semibold">
              You've already reserved {eligibility.reserved.apartment.building}, unit{' '}
              {eligibility.reserved.apartment.number}. One deposit reserves one unit.
            </p>
          )}
        </form>
      )}

      {reserveError && (
        <p className="mt-4 rounded-md border-2 border-brand bg-paper p-4 font-semibold">
          Couldn't reserve: {reserveError}
        </p>
      )}

      <div className="mt-8">
        {error ? (
          <p className="rounded-md border-2 border-brand bg-paper p-5">
            Could not load apartments: {error}
          </p>
        ) : loading ? (
          <p className="text-muted">Loading apartments…</p>
        ) : apartments.length === 0 ? (
          <p className="rounded-md border-2 border-line bg-paper p-5 text-muted">
            No apartments are currently available.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {apartments.map((apartment) => (
              <article key={apartment.id} className="rounded-md border-2 border-ink bg-paper p-5">
                <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">
                  {apartment.building}
                </p>
                <h2 className="mt-2 text-2xl font-bold">Unit {apartment.number}</h2>
                <p className="mt-2 text-muted">
                  {apartment.bedrooms} {apartment.bedrooms === 1 ? 'bedroom' : 'bedrooms'}
                </p>
                <p className="mt-4 text-xl font-semibold">
                  {formatDollars(apartment.price_cents)}
                  <span className="text-sm font-normal text-muted"> / month</span>
                </p>
                {!reserved && (
                  <button
                    onClick={() => reserve(apartment)}
                    disabled={!canReserve || reservingId !== null}
                    title={canReserve ? '' : 'Check your deposit above first'}
                    className="mt-4 rounded bg-brand px-4 py-2 font-semibold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {reservingId === apartment.id ? 'Reserving…' : 'Reserve'}
                  </button>
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

const INPUT = 'mt-1 block w-full rounded border-2 border-line bg-white px-3 py-2 font-normal'
