/**
 * Talking to the backend.
 *
 * api('/apartments') fetches /api/apartments, which Vite forwards to
 * GET /apartments on the FastAPI backend (see vite.config.ts).
 *
 *   const apartments = await api<Apartment[]>('/apartments')
 *   await api('/admin/apartments', { method: 'POST', body: JSON.stringify(newApartment) })
 *
 * If the API answers with an error, api() throws an Error with the API's message.
 */
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail ?? `${response.status} ${response.statusText}`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (response.status === 204) {
    return undefined as T // "No Content", e.g. after a DELETE
  }
  return response.json() as Promise<T>
}

// These match the schemas in backend/app/schemas.py.
// If you change one side, change the other.

export type Apartment = {
  id: number
  number: string
  building: string
  bedrooms: number
  price_cents: number
  available: boolean
}

/** What the staff form sends to add an apartment */
export type NewApartment = Omit<Apartment, 'id' | 'available'>

export type Reservation = {
  id: number
  apartment_id: number
  student_name: string
  student_email: string
  paid: boolean
  status: 'held' | 'confirmed' | 'expired' | 'cancelled'
  expires_at: string | null
  created_at: string
}

export type ReservationCreate = {
  apartment_id: number
  student_name: string
  student_email: string
}

/** Prices are stored in cents. formatDollars(72500) gives "$725". */
export function formatDollars(cents: number): string {
  return (cents / 100).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
  })
}
