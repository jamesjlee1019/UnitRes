import { useEffect, useState } from 'react'
import { api, formatDollars, type Apartment } from '../api.ts'

/**
 * BOOKING TEAM: the list of available apartments.
 */
export default function ApartmentsPage() {
  const [apartments, setApartments] = useState<Apartment[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api<Apartment[]>('/apartments')
      .then(setApartments)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <section>
      <h1 className="text-4xl font-bold tracking-tight">Available apartments</h1>
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
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
