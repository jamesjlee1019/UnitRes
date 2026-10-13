import TodoNote from '../components/TodoNote.tsx'

/**
 * ADMIN TEAM: the staff back office. It can be ugly.
 *
 * Week 1:
 *   1. Build POST /admin/apartments in backend/app/routers/admin.py
 *   2. Add a form here with number, building, bedrooms and price. On submit:
 *        await api('/admin/apartments', { method: 'POST', body: JSON.stringify(newApartment) })
 *      The API wants the price in cents, so $950 is 95000. (See NewApartment in src/api.ts.)
 *   3. Check it worked with GET /health at http://localhost:8000/docs (the count goes up).
 *   4. Delete the <TodoNote />.
 *
 * Week 2: remove an apartment, and list who reserved what.
 */
export default function AdminPage() {
  return (
    <section>
      <h1 className="text-4xl font-bold tracking-tight">Staff</h1>
      <div className="mt-8">
        <TodoNote team="Admin" />
      </div>
    </section>
  )
}
