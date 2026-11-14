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

/**
 * Students pay the security deposit in JSM's Entrata first. Reserve only works once
 * that deposit has shown up here, and then it's confirmed right away. No holds.
 */
export type ReservationStatus = 'confirmed' | 'cancelled'

/** What the student sees: POST /reservations returns this */
export type StudentReservation = {
  id: number
  status: ReservationStatus
  created_at: string
  apartment: Apartment
}

/**
 * GET /eligibility?email=... : turn the Reserve buttons on only when can_reserve is true.
 * no_deposit: send them to entrata_application_url to apply and pay, then check again.
 */
export type Eligibility = {
  can_reserve: boolean
  reason: 'ok' | 'no_deposit' | 'already_reserved'
  reserved: StudentReservation | null
  entrata_application_url: string
}

/** What a student types to reserve. The email must match their Entrata application. */
export type NewReservation = {
  apartment_id: number
  student_name: string
  student_email: string
}

/** A full reservation, for the staff page (GET /admin/reservations) */
export type Reservation = {
  id: number
  apartment_id: number
  student_name: string
  student_email: string
  status: ReservationStatus
  created_at: string
  entrata_unit_marked: boolean
  apartment: Apartment
  deposit: { id: number; entrata_id: string; amount_cents: number; paid_at: string } | null
}

/** A security deposit paid in Entrata, for the staff page (GET /admin/deposits) */
export type Deposit = {
  id: number
  entrata_id: string
  payer_email: string
  amount_cents: number
  paid_at: string
  received_at: string
  refunded_at: string | null
  active_reservation_id: number | null // empty: not reserving anything yet
}

/** Prices are stored in cents. formatDollars(72500) gives "$725". */
export function formatDollars(cents: number): string {
  return (cents / 100).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
  })
}
