import { NavLink, Route, Routes } from 'react-router'
import AdminPage from './pages/AdminPage.tsx'
import ApartmentsPage from './pages/ApartmentsPage.tsx'
import CheckoutPage from './pages/CheckoutPage.tsx'
import CheckoutSuccessPage from './pages/CheckoutSuccessPage.tsx'
import HomePage from './pages/HomePage.tsx'

const NAV_LINKS = [
  { to: '/', label: 'General application' },
  { to: '/apartments', label: 'Apartments' },
  { to: '/setup', label: 'Setup' },
]

export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line">
        <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-4">
          <span className="mr-2 font-mono text-xs tracking-[0.2em]">JSM UNITRES</span>
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end
              className={({ isActive }) =>
                isActive ? 'font-semibold text-brand' : 'text-muted hover:text-ink'
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-10">
        {/* Adding a page? Make it in src/pages/ and add a <Route> for it here. */}
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/setup" element={<HomePage setupOnly />} />
          <Route path="/apartments" element={<ApartmentsPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/checkout/success" element={<CheckoutSuccessPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<p className="text-muted">No page here.</p>} />
        </Routes>
      </main>
    </div>
  )
}
