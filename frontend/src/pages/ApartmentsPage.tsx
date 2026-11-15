import { useEffect, useMemo, useState, type FormEvent } from 'react'
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
 * Students pay their security deposit in JSM's Entrata application first. Here they
 * pick a unit and type the email from that application. We check GET /eligibility,
 * then POST /reservations, which is confirmed right away. No holds.
 */
export default function ApartmentsPage() {
  const [apartments, setApartments] = useState<Apartment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedApartmentId, setSelectedApartmentId] = useState<number | null>(null)
  const [studentName, setStudentName] = useState('')
  const [studentEmail, setStudentEmail] = useState('')
  const [reservation, setReservation] = useState<StudentReservation | null>(null)
  const [reservationError, setReservationError] = useState<string | null>(null)
  // Where to apply and pay, shown when we haven't seen their deposit yet
  const [applyUrl, setApplyUrl] = useState<string | null>(null)
  const [reserving, setReserving] = useState(false)
  const [search, setSearch] = useState('')
  const [bedroomFilter, setBedroomFilter] = useState('all')
  const [sortBy, setSortBy] = useState('price-asc')

  async function loadApartments() {
    setLoading(true)
    setError(null)
    try {
      setApartments(await api<Apartment[]>('/apartments'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load apartments.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    api<Apartment[]>('/apartments')
      .then(setApartments)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const visibleApartments = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()
    return apartments
      .filter((apartment) => {
        const matchesSearch =
          !normalizedSearch ||
          `${apartment.building} ${apartment.number}`.toLowerCase().includes(normalizedSearch)
        const matchesBedrooms =
          bedroomFilter === 'all' || apartment.bedrooms === Number(bedroomFilter)
        return matchesSearch && matchesBedrooms
      })
      .sort((a, b) => {
        if (sortBy === 'price-desc') return b.price_cents - a.price_cents
        if (sortBy === 'bedrooms') return b.bedrooms - a.bedrooms || a.price_cents - b.price_cents
        return a.price_cents - b.price_cents
      })
  }, [apartments, bedroomFilter, search, sortBy])

  const bedroomOptions = [...new Set(apartments.map(({ bedrooms }) => bedrooms))].sort(
    (a, b) => a - b,
  )

  function clearFilters() {
    setSearch('')
    setBedroomFilter('all')
    setSortBy('price-asc')
  }

  function startReservation(apartmentId: number) {
    setSelectedApartmentId(apartmentId)
    setReservation(null)
    setReservationError(null)
    setApplyUrl(null)
  }

  async function submitReservation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (selectedApartmentId === null) return

    const request: NewReservation = {
      apartment_id: selectedApartmentId,
      student_name: studentName.trim(),
      student_email: studentEmail.trim(),
    }
    setReserving(true)
    setReservationError(null)
    setApplyUrl(null)
    try {
      // Has this email paid a deposit that isn't reserving anything yet?
      const eligibility = await api<Eligibility>(
        `/eligibility?email=${encodeURIComponent(request.student_email)}`,
      )
      if (eligibility.reason === 'no_deposit') {
        setReservationError(
          `We haven't seen a security deposit from ${request.student_email} yet. Apply and pay ` +
            "it in JSM's application with this email, then come back. It can take a few " +
            'minutes to show up here.',
        )
        setApplyUrl(eligibility.entrata_application_url)
        return
      }
      if (eligibility.reason === 'already_reserved') {
        const unit = eligibility.reserved?.apartment
        setReservationError(
          `${request.student_email} has already reserved ` +
            (unit ? `Unit ${unit.number} in ${unit.building}` : 'a unit') +
            '. One security deposit reserves one unit.',
        )
        return
      }

      const created = await api<StudentReservation>('/reservations', {
        method: 'POST',
        body: JSON.stringify(request),
      })
      setReservation(created)
      setApartments((current) => current.filter(({ id }) => id !== created.apartment.id))
      setSelectedApartmentId(null)
      setStudentName('')
      setStudentEmail('')
    } catch (err) {
      setReservationError(err instanceof Error ? err.message : 'Could not reserve this apartment.')
    } finally {
      setReserving(false)
    }
  }

  return (
    <section>
      <div className="overflow-hidden rounded-lg border-2 border-ink bg-ink px-6 py-8 text-cream sm:px-10">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand">Find your next home</p>
        <h1 className="mt-3 max-w-2xl text-4xl font-bold tracking-tight sm:text-5xl">
          Apartments that feel like home.
        </h1>
        <p className="mt-4 max-w-xl text-cream/70">
          Paid your security deposit in JSM's application? Pick a unit here and it's yours right away.
        </p>
        <div className="mt-7 flex flex-wrap gap-6 text-sm">
          <div>
            <p className="font-mono text-2xl font-bold text-cream">{apartments.length}</p>
            <p className="text-cream/60">available now</p>
          </div>
          <div>
            <p className="font-mono text-2xl font-bold text-cream">1 unit</p>
            <p className="text-cream/60">per deposit</p>
          </div>
          <div>
            <p className="font-mono text-2xl font-bold text-cream">Instant</p>
            <p className="text-cream/60">confirmation</p>
          </div>
        </div>
      </div>

      {reservation && (
        <div className="mt-6 rounded-md border-2 border-emerald-700 bg-emerald-50 p-5">
          <p className="font-mono text-xs uppercase tracking-[0.2em] text-emerald-700">Reserved</p>
          <h2 className="mt-1 text-xl font-bold">
            Unit {reservation.apartment.number} in {reservation.apartment.building} is yours.
          </h2>
          <p className="mt-2 text-sm text-muted">
            {reservation.apartment.bedrooms}{' '}
            {reservation.apartment.bedrooms === 1 ? 'bedroom' : 'bedrooms'} ·{' '}
            {formatDollars(reservation.apartment.price_cents)}/month. It's off the list, so nobody
            else can reserve it.
          </p>
        </div>
      )}

      <div className="mt-8">
        {error ? (
          <div className="rounded-md border-2 border-danger bg-paper p-5">
            <p>Could not load apartments: {error}</p>
            <button type="button" className="mt-3 font-semibold text-brand-ink underline" onClick={() => void loadApartments()}>
              Try again
            </button>
          </div>
        ) : loading ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {[1, 2, 3, 4].map((item) => (
              <div key={item} className="h-56 animate-pulse rounded-md border-2 border-line bg-paper" />
            ))}
          </div>
        ) : apartments.length === 0 ? (
          <p className="rounded-md border-2 border-line bg-paper p-5 text-muted">
            No apartments are currently available.
          </p>
        ) : (
          <>
            <div className="rounded-md border-2 border-line bg-paper p-4">
              <div className="flex flex-col gap-3 lg:flex-row">
                <label className="min-w-0 flex-1">
                  <span className="sr-only">Search apartments</span>
                  <input
                    className="w-full rounded-md border border-line bg-cream px-3 py-2.5 outline-none ring-brand-ink placeholder:text-muted focus:ring-2"
                    placeholder="Search by building or unit…"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </label>
                <label>
                  <span className="sr-only">Filter by bedrooms</span>
                  <select
                    className="w-full rounded-md border border-line bg-cream px-3 py-2.5 outline-none focus:ring-2 focus:ring-brand-ink"
                    value={bedroomFilter}
                    onChange={(event) => setBedroomFilter(event.target.value)}
                  >
                    <option value="all">Any bedrooms</option>
                    {bedroomOptions.map((bedrooms) => (
                      <option key={bedrooms} value={bedrooms}>
                        {bedrooms} {bedrooms === 1 ? 'bedroom' : 'bedrooms'}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span className="sr-only">Sort apartments</span>
                  <select
                    className="w-full rounded-md border border-line bg-cream px-3 py-2.5 outline-none focus:ring-2 focus:ring-brand-ink"
                    value={sortBy}
                    onChange={(event) => setSortBy(event.target.value)}
                  >
                    <option value="price-asc">Price: low to high</option>
                    <option value="price-desc">Price: high to low</option>
                    <option value="bedrooms">Most bedrooms</option>
                  </select>
                </label>
              </div>
              <p className="mt-3 text-sm text-muted">
                Showing {visibleApartments.length} of {apartments.length} available apartments
                {(search || bedroomFilter !== 'all') && (
                  <button type="button" className="ml-2 font-semibold text-brand-ink underline" onClick={clearFilters}>
                    Clear filters
                  </button>
                )}
              </p>
            </div>

            {visibleApartments.length === 0 ? (
              <div className="mt-4 rounded-md border-2 border-line bg-paper p-8 text-center">
                <p className="text-lg font-semibold">No apartments match those filters.</p>
                <button type="button" className="mt-3 font-semibold text-brand-ink underline" onClick={clearFilters}>
                  Show all apartments
                </button>
              </div>
            ) : (
              <div className="mt-4 grid items-start gap-5 sm:grid-cols-2">
                {visibleApartments.map((apartment) => (
                  <article key={apartment.id} className="group rounded-md border-2 border-ink bg-paper p-5 transition-shadow hover:shadow-[5px_5px_0_#1c1a17]">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-mono text-xs uppercase tracking-[0.2em] text-brand-ink">
                          {apartment.building}
                        </p>
                        <h2 className="mt-2 text-2xl font-bold">Unit {apartment.number}</h2>
                      </div>
                      <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-800">
                        Available
                      </span>
                    </div>
                    <div className="mt-6 flex items-end justify-between border-t border-line pt-4">
                      <div>
                        <p className="text-sm text-muted">
                          {apartment.bedrooms} {apartment.bedrooms === 1 ? 'bedroom' : 'bedrooms'}
                        </p>
                        <p className="mt-1 text-xl font-semibold">
                          {formatDollars(apartment.price_cents)}
                          <span className="text-sm font-normal text-muted"> / month</span>
                        </p>
                      </div>
                      <button
                        type="button"
                        className="rounded-md bg-brand px-4 py-2 font-semibold text-ink transition-colors hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
                        onClick={() => startReservation(apartment.id)}
                        disabled={reserving}
                      >
                        Reserve
                      </button>
                    </div>
                    {selectedApartmentId === apartment.id && (
                      <form className="mt-5 space-y-3 border-t border-line pt-5" onSubmit={submitReservation}>
                        <p className="text-sm font-semibold">
                          Use the email from your JSM application, so we can find your deposit.
                        </p>
                    <label className="block text-sm font-semibold">
                      Name
                      <input
                        className="mt-1 block w-full rounded-md border border-line bg-cream px-3 py-2 font-normal"
                        value={studentName}
                        onChange={(event) => setStudentName(event.target.value)}
                        required
                        maxLength={200}
                      />
                    </label>
                    <label className="block text-sm font-semibold">
                      Email
                      <input
                        type="email"
                        className="mt-1 block w-full rounded-md border border-line bg-cream px-3 py-2 font-normal"
                        value={studentEmail}
                        onChange={(event) => setStudentEmail(event.target.value)}
                        required
                      />
                    </label>
                    {reservationError && (
                      <p className="text-sm text-danger">
                        {reservationError}
                        {applyUrl && (
                          <>
                            {' '}
                            <a className="font-semibold underline" href={applyUrl} target="_blank" rel="noreferrer">
                              Go to JSM's application
                            </a>
                          </>
                        )}
                      </p>
                    )}
                    <div className="flex gap-3">
                      <button
                        type="submit"
                        className="rounded-md bg-ink px-4 py-2 font-semibold text-cream disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={reserving}
                      >
                        {reserving ? 'Reserving…' : 'Confirm reservation'}
                      </button>
                      <button
                        type="button"
                        className="px-2 py-2 text-sm text-muted hover:text-ink"
                        onClick={() => setSelectedApartmentId(null)}
                        disabled={reserving}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                    )}
                  </article>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </section>
  )
}
