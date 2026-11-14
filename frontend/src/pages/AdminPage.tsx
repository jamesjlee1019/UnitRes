import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import {
  api,
  formatDollars,
  type Apartment,
  type ApartmentUpdate,
  type NewApartment,
  type Reservation,
} from '../api.ts'

/**
 * ADMIN TEAM: the staff back office. It can be ugly.
 *
 * Week 1: a form that adds an apartment with POST /admin/apartments.
 *   The API wants the price in cents, so $950 is sent as 95000.
 *
 * Week 2: remove an apartment, and list who reserved what.
 *
 * Next: mark an apartment available or unavailable with PATCH /admin/apartments/{id}.
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

  async function handleDelete(id: number) {
    if (!confirm('Delete this reservation? This cannot be undone.')) return
    try {
      await api<null>(`/admin/reservations/${id}`, { method: 'DELETE' })
      setReservations((prev) => prev.filter((r) => r.id !== id))
    } catch (err) {
      alert(`Couldn't delete: ${(err as Error).message}`)
    }
  }

  useEffect(() => {
    loadReservations()
  }, [])

  const [apartments, setApartments] = useState<Apartment[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  // The apartment whose Remove or Mark button is waiting on the API
  const [busyId, setBusyId] = useState<number | null>(null)
  const [rowMessage, setRowMessage] = useState<string | null>(null)

  function loadApartments() {
    return fetchApartments()
      .then((allApartments) => {
        setApartments(allApartments)
        setLoadError(null)
      })
      .catch((err: Error) => setLoadError(err.message))
  }

  useEffect(() => {
    let ignore = false // the page closed before the apartments arrived
    fetchApartments()
      .then((allApartments) => {
        if (!ignore) setApartments(allApartments)
      })
      .catch((err: Error) => {
        if (!ignore) setLoadError(err.message)
      })
    return () => {
      ignore = true
    }
  }, [])

  async function handleRemove(apartment: Apartment) {
    if (!window.confirm(`Remove ${apartment.number} in ${apartment.building}?`)) return
    setBusyId(apartment.id)
    setRowMessage(null)
    try {
      await api(`/admin/apartments/${apartment.id}`, { method: 'DELETE' })
      setRowMessage(`Removed ${apartment.number}.`)
      await loadApartments()
    } catch (err) {
      // e.g. 409 when the apartment still has reservations
      setRowMessage(`Couldn't remove ${apartment.number}: ${(err as Error).message}`)
    } finally {
      setBusyId(null)
    }
  }

  async function handleToggleAvailable(apartment: Apartment) {
    const changes: ApartmentUpdate = { available: !apartment.available }
    setBusyId(apartment.id)
    setRowMessage(null)
    try {
      const updated = await api<Apartment>(`/admin/apartments/${apartment.id}`, {
        method: 'PATCH',
        body: JSON.stringify(changes),
      })
      setApartments((current) =>
        current.map((other) => (other.id === updated.id ? updated : other)),
      )
      setRowMessage(
        `Marked ${updated.number} ${updated.available ? 'available' : 'unavailable'}.`,
      )
    } catch (err) {
      setRowMessage(`Couldn't change ${apartment.number}: ${(err as Error).message}`)
    } finally {
      setBusyId(null)
    }
  }

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
      await loadApartments()
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
            max={100000}
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

      {loadError && (
        <p className="mt-8 font-semibold text-brand">Couldn't load apartments: {loadError}</p>
      )}

      <h2 className="mt-10 text-2xl font-bold tracking-tight">All apartments</h2>
      <div className="mt-4 overflow-x-auto">
        <table className={TABLE}>
          <thead>
            <tr>
              <th className={CELL}>Number</th>
              <th className={CELL}>Building</th>
              <th className={CELL}>Bedrooms</th>
              <th className={CELL}>Rent</th>
              <th className={CELL}>Available</th>
              <th className={CELL}></th>
            </tr>
          </thead>
          <tbody>
            {apartments.map((apartment) => (
              <tr key={apartment.id}>
                <td className={CELL}>{apartment.number}</td>
                <td className={CELL}>{apartment.building}</td>
                <td className={CELL}>{apartment.bedrooms}</td>
                <td className={CELL}>{formatDollars(apartment.price_cents)}/month</td>
                <td className={CELL}>{apartment.available ? 'Yes' : 'No'}</td>
                <td className={CELL}>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={busyId === apartment.id}
                      onClick={() => handleToggleAvailable(apartment)}
                      className={ROW_BUTTON}
                    >
                      {apartment.available ? 'Mark unavailable' : 'Mark available'}
                    </button>
                    <button
                      type="button"
                      disabled={busyId === apartment.id}
                      onClick={() => handleRemove(apartment)}
                      className={ROW_BUTTON}
                    >
                      Remove
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rowMessage && <p className="mt-4 font-semibold">{rowMessage}</p>}

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
              {['Student', 'Email', 'Apartment', 'Status', 'Paid', 'Reserved on', ''].map((h) => (
                <th key={h} className="border border-line px-3 py-2 text-left">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reservations.map((r) => (
              <tr key={r.id}>
                <td className="border border-line px-3 py-2">{r.student_name}</td>
                <td className="border border-line px-3 py-2">{r.student_email}</td>
                <td className="border border-line px-3 py-2">#{r.apartment_id}</td>
                <td className="border border-line px-3 py-2">{r.status}</td>
                <td className="border border-line px-3 py-2">{r.deposit ? 'Yes' : 'No'}</td>
                <td className="border border-line px-3 py-2">{new Date(r.created_at).toLocaleDateString()}</td>
                <td className="border border-line px-3 py-2">
                  <button
                    onClick={() => handleDelete(r.id)}
                    disabled={r.status === 'confirmed'}
                    title={r.status === 'confirmed' ? 'Cancel this reservation before deleting it' : ''}
                    className="font-semibold text-brand underline disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function fetchApartments() {
  return api<Apartment[]>('/admin/apartments')
}

const INPUT = 'mt-1 block w-full rounded border-2 border-line bg-white px-3 py-2'
const TABLE = 'w-full border-collapse rounded-md border-2 border-ink bg-paper text-left'
const CELL = 'border-b border-line px-3 py-2'
const ROW_BUTTON =
  'whitespace-nowrap rounded border-2 border-ink px-3 py-1 text-sm font-semibold hover:bg-ink hover:text-white disabled:opacity-50'

function Field(props: { label: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-semibold">
      {props.label}
      {props.children}
    </label>
  )
}
