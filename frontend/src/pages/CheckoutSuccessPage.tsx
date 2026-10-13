import TodoNote from '../components/TodoNote.tsx'

/**
 * PAYMENTS TEAM: where Stripe sends the student after they pay.
 *
 * Week 1: say something friendly, like "Payment received", and delete the <TodoNote />.
 */
export default function CheckoutSuccessPage() {
  return (
    <section>
      <h1 className="text-4xl font-bold tracking-tight">Payment received</h1>
      <div className="mt-8">
        <TodoNote team="Payments" />
      </div>
    </section>
  )
}
