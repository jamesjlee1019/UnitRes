import TodoNote from '../components/TodoNote.tsx'

/**
 * PAYMENTS TEAM: sends the student to Stripe to pay the application fee.
 *
 * Week 1:
 *   1. Build POST /payments/checkout-session in backend/app/routers/payments.py
 *   2. Add a button here that calls it:
 *        const { url } = await api<{ url: string }>('/payments/checkout-session', { method: 'POST' })
 *      and then sends the browser there: window.location.href = url
 *   3. Pay with card 4242 4242 4242 4242, any future date, any CVC.
 *      Stripe sends you back to /checkout/success (CheckoutSuccessPage.tsx).
 *   4. Delete the <TodoNote />.
 *
 * Week 2: start this from the Reserve button instead, and mark the reservation as paid.
 */
export default function CheckoutPage() {
  return (
    <section>
      <h1 className="text-4xl font-bold tracking-tight">Pay the application fee</h1>
      <div className="mt-8">
        <TodoNote team="Payments" />
      </div>
    </section>
  )
}
