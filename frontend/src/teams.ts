/** Each team's week-1 goal and where its code goes. Shown on the home page and the team pages. */

export type TeamName = 'Booking' | 'Payments' | 'Admin' | 'Accounts'

type Team = {
  goal: string
  files: string[]
  page?: string // the website page to open
  command?: string // or the command to run
}

export const TEAMS: Record<TeamName, Team> = {
  Booking: {
    goal: 'The apartments page shows the available units from the database.',
    files: ['backend/app/routers/booking.py', 'frontend/src/pages/ApartmentsPage.tsx'],
    page: '/apartments',
  },
  Payments: {
    goal: 'A button opens Stripe Checkout in test mode, and card 4242 goes through to a success page.',
    files: [
      'backend/app/routers/payments.py',
      'frontend/src/pages/CheckoutPage.tsx',
      'frontend/src/pages/CheckoutSuccessPage.tsx',
    ],
    page: '/checkout',
  },
  Admin: {
    goal: 'A form on the staff page adds an apartment to the database.',
    files: ['backend/app/routers/admin.py', 'frontend/src/pages/AdminPage.tsx'],
    page: '/admin',
  },
  Accounts: {
    goal: 'A script sends the "you\'re reserved" email, with the Calendly link, to your own inbox.',
    files: ['backend/scripts/send_test_email.py'],
    command: 'docker compose exec api python scripts/send_test_email.py you@stanford.edu',
  },
}
