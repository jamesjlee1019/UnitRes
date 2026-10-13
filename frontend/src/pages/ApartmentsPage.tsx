import TodoNote from '../components/TodoNote.tsx'

/**
 * BOOKING TEAM: the list of available apartments (the mock on kickoff slide 2).
 *
 * Week 1:
 *   1. Build GET /apartments in backend/app/routers/booking.py
 *   2. Load it here the same way HomePage.tsx loads /health:
 *      useState + useEffect + api<Apartment[]>('/apartments')
 *   3. Show one row per apartment. formatDollars() in src/api.ts turns 72500 into "$725".
 *   4. Delete the <TodoNote />.
 *
 * Week 2: a Reserve button on each row.
 */
export default function ApartmentsPage() {
  return (
    <section>
      <h1 className="text-4xl font-bold tracking-tight">Available apartments</h1>
      <div className="mt-8">
        <TodoNote team="Booking" />
      </div>
    </section>
  )
}
