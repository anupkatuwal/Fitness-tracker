import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="py-20 text-center">
      <Compass className="mx-auto mb-4 h-12 w-12 text-slate-600" aria-hidden="true" />
      <h1 className="text-3xl font-bold text-white">Page not found</h1>
      <p className="mx-auto mt-2 max-w-md text-slate-400">
        That route does not exist. Head back to the dashboard and try again.
      </p>
      <Link
        to="/"
        className="mt-6 inline-block rounded-lg bg-accent-strong px-5 py-2.5 text-sm font-semibold text-ink hover:bg-accent"
      >
        Back to dashboard
      </Link>
    </div>
  )
}
