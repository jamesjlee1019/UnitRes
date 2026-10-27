import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { api, formatDollars, type Apartment, type NewApartment } from '../api.ts'

/**
 * ADMIN TEAM: the staff back office. It can be ugly.
 *
 * Week 1: a form that adds an apartment with POST /admin/apartments.
 *   The API wants the price in cents, so $950 is sent as 95000.
 *
 * Week 2: remove an apartment, and list who reserved what.
 */
export default function AdminPage() {
  const [number, setNumber] = useState('')
  const [building, setBuilding] = useState('')
  const [bedrooms, setBedrooms] = useState('')
  const [price, setPrice] = useState('')
  const [saving, setSaving] = useState(false)
  const [added, setAdded] = useState<Apartment | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reservations, setReservations] = useState<Reservation[]>([])
  const [loadingReservations, setLoadingReservations] = useState(true)
  const [reservationsError, setReservationsError] = useState<string | null>(null)

  async function loadReservations() {
    setLoadingReservations(true)
    setReservationsError(null)
    try {
      setReservations(await api<Reservation[]>('/admin/reservations'))
    } catch (err) {
      setReservationsError((err as Error).message)
    } finally {
      setLoadingReservations(false)
    }
  }

  useEffect(() => {
    loadReservations()
  }, [])
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setAdded(null)
    setError(null)

    const newApartment: NewApartment = {
      number: number.trim(),
      building: building.trim(),
      bedrooms: Number(bedrooms),
      price_cents: Math.round(Number(price) * 100),
    }

    try {
      const apartment = await api<Apartment>('/admin/apartments', {
        method: 'POST',
        body: JSON.stringify(newApartment),
      })
      setAdded(apartment)
      setNumber('')
      setBuilding('')
      setBedrooms('')
      setPrice('')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <section>
      <h1 className="text-4xl font-bold tracking-tight">Staff</h1>

      <h2 className="mt-8 text-2xl font-bold tracking-tight">Add an apartment</h2>
      <form
        onSubmit={handleSubmit}
        className="mt-4 grid max-w-md gap-4 rounded-md border-2 border-ink bg-paper p-5"
      >
        <Field label="Number">
          <input
            className={INPUT}
            required
            maxLength={20}
            placeholder="D-410"
            value={number}
            onChange={(e) => setNumber(e.target.value)}
          />
        </Field>
        <Field label="Building">
          <input
            className={INPUT}
            required
            maxLength={100}
            placeholder="Building D"
            value={building}
            onChange={(e) => setBuilding(e.target.value)}
          />
        </Field>
        <Field label="Bedrooms">
          <input
            className={INPUT}
            type="number"
            required
            min={0}
            max={10}
            step={1}
            placeholder="2"
            value={bedrooms}
            onChange={(e) => setBedrooms(e.target.value)}
          />
        </Field>
        <Field label="Monthly rent ($)">
          <input
            className={INPUT}
            type="number"
            required
            min={0.01}
            step={0.01}
            placeholder="950"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </Field>
        <button
          type="submit"
          disabled={saving}
          className="rounded bg-brand px-4 py-2 font-semibold text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {saving ? 'Adding…' : 'Add apartment'}
        </button>
      </form>

      {added && (
        <p className="mt-4 font-semibold">
          Added {added.number} in {added.building} ({added.bedrooms} bed,{' '}
          {formatDollars(added.price_cents)}/month) as apartment #{added.id}.
        </p>
      )}
      {error && <p className="mt-4 font-semibold text-brand">Couldn't add it: {error}</p>}
      <h2 className="mt-10 text-2xl font-bold tracking-tight">Reservations</h2>
      <button
        onClick={loadReservations}
        className="mt-2 text-sm font-semibold underline"
      >
        Refresh
      </button>

      {loadingReservations ? (
        <p className="mt-4">Loading…</p>
      ) : reservationsError ? (
        <p className="mt-4 font-semibold text-brand">Couldn't load reservations: {reservationsError}</p>
      ) : reservations.length === 0 ? (
        <p className="mt-4">No reservations yet.</p>
      ) : (
        <table className="mt-4 border-2 border-ink bg-paper text-sm">
          <thead>
            <tr>
              {Object.keys(reservations[0]).map((key) => (
                <th key={key} className="border border-line px-3 py-2 text-left">{key}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reservations.map((r, i) => (
              <tr key={i}>
                {Object.keys(reservations[0]).map((key) => (
                  <td key={key} className="border border-line px-3 py-2">{String(r[key] ?? '')}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

const INPUT = 'mt-1 block w-full rounded border-2 border-line bg-white px-3 py-2'

function Field(props: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-semibold">
      {props.label}
      {props.children}
    </label>
  )
}
type Reservation = Record<string, unknown>