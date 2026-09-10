import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import {
  Calculator,
  Dumbbell,
  FlaskConical,
  LayoutDashboard,
  LogOut,
  Menu,
  Shield,
  User,
  Utensils,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/macros', label: 'Macro Tracker', icon: Utensils },
  { to: '/exercises', label: 'Exercise Directory', icon: Dumbbell },
  { to: '/peds', label: 'PED Library', icon: FlaskConical },
  { to: '/calculators', label: 'Calculators', icon: Calculator },
]

function NavItem({ item, onNavigate }) {
  const Icon = item.icon
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
          isActive
            ? 'bg-accent-strong/15 text-accent'
            : 'text-slate-400 hover:bg-surface-2 hover:text-white'
        }`
      }
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
      {item.label}
    </NavLink>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()

  // Close the mobile menu whenever the route changes.
  useEffect(() => setMenuOpen(false), [location.pathname])

  return (
    <div className="flex min-h-screen flex-col bg-base">
      <header className="sticky top-0 z-40 border-b border-line bg-base/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
          <Link to="/" className="flex shrink-0 items-center gap-2">
            <Shield className="h-6 w-6 text-accent" aria-hidden="true" />
            <span className="text-lg font-bold tracking-tight text-white">
              Vanguard<span className="text-accent"> Fitness</span>
            </span>
          </Link>

          <nav className="ml-4 hidden flex-1 items-center gap-1 lg:flex" aria-label="Main">
            {NAV_ITEMS.map((item) => (
              <NavItem key={item.to} item={item} />
            ))}
          </nav>

          <div className="ml-auto hidden items-center gap-3 lg:flex">
            {user ? (
              <>
                <Link
                  to="/profile"
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-300 hover:text-white"
                >
                  <User className="h-4 w-4" aria-hidden="true" />
                  {user.username}
                </Link>
                <button
                  onClick={logout}
                  className="flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm text-slate-300 transition-colors hover:border-hazard hover:text-white"
                >
                  <LogOut className="h-4 w-4" aria-hidden="true" />
                  Sign out
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="rounded-lg bg-accent-strong px-4 py-2 text-sm font-semibold text-ink transition-colors hover:bg-accent"
              >
                Sign in
              </Link>
            )}
          </div>

          <button
            className="ml-auto rounded-lg border border-line p-2 text-slate-300 lg:hidden"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          >
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {menuOpen ? (
          <nav id="mobile-nav" className="border-t border-line px-4 py-3 lg:hidden" aria-label="Mobile">
            <div className="space-y-1">
              {NAV_ITEMS.map((item) => (
                <NavItem key={item.to} item={item} onNavigate={() => setMenuOpen(false)} />
              ))}
            </div>
            <div className="mt-3 border-t border-line pt-3">
              {user ? (
                <div className="flex items-center justify-between">
                  <Link to="/profile" className="text-sm text-slate-300">
                    Signed in as <span className="font-semibold text-white">{user.username}</span>
                  </Link>
                  <button onClick={logout} className="text-sm font-semibold text-hazard">
                    Sign out
                  </button>
                </div>
              ) : (
                <Link
                  to="/login"
                  className="block rounded-lg bg-accent-strong px-4 py-2 text-center text-sm font-semibold text-ink"
                >
                  Sign in
                </Link>
              )}
            </div>
          </nav>
        ) : null}
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">
        <Outlet />
      </main>

      <footer className="border-t border-line px-4 py-6 text-center text-xs text-slate-500 sm:px-6">
        <p>
          Vanguard Fitness is an educational tool. Nothing here is medical advice. Talk to a
          qualified physician before changing how you train, eat, or supplement.
        </p>
      </footer>
    </div>
  )
}
