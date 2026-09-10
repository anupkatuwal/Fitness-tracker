import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertOctagon, FlaskConical, Search, ShieldAlert } from 'lucide-react'
import {
  Card,
  EmptyState,
  ErrorNote,
  Field,
  Input,
  Pill,
  SectionHeading,
  Select,
  Spinner,
} from '../components/ui.jsx'
import { HazardBanner } from '../components/HazardCards.jsx'
import { useDebounced } from '../hooks/useDebounced.js'
import { api } from '../lib/api.js'

export default function PedLibrary() {
  const [categories, setCategories] = useState([])
  const [category, setCategory] = useState('all')
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search, 300)

  const [profiles, setProfiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.pedCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    setError('')

    api
      .peds({ category, search: debouncedSearch.trim() }, controller.signal)
      .then((data) => {
        setProfiles(data)
        setLoading(false)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setError(err.message || 'Could not load the compound library.')
        setLoading(false)
      })

    return () => controller.abort()
  }, [category, debouncedSearch])

  return (
    <div className="space-y-8">
      <SectionHeading
        icon={FlaskConical}
        title="PED & Peptide Library"
        subtitle="An educational reference. Every compound page states its cardiovascular, endocrine and hepatic risks."
      />

      <HazardBanner />

      <Card className="p-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Search compounds" htmlFor="ped-search">
            <div className="relative">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
                aria-hidden="true"
              />
              <Input
                id="ped-search"
                className="pl-9"
                placeholder="Name or alias..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </Field>
          <Field label="Category" htmlFor="ped-category">
            <Select
              id="ped-category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="all">All categories</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </Card>

      <ErrorNote>{error}</ErrorNote>

      {loading ? (
        <Spinner label="Loading compounds" />
      ) : profiles.length === 0 ? (
        <EmptyState icon={FlaskConical} title="No compounds match that search">
          Try a different name or clear the category filter.
        </EmptyState>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {profiles.map((profile) => (
            <Link
              key={profile.id}
              to={`/peds/${profile.slug}`}
              className="group flex h-full flex-col overflow-hidden rounded-2xl border-2 border-hazard/60 bg-surface transition-colors hover:border-hazard"
            >
              {/* Every card in the list carries the hazard strip, so the warning
                  is never something a user can reach a compound without seeing. */}
              <div className="flex items-center gap-2 bg-[#991b1b] px-4 py-2 text-white">
                <AlertOctagon className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span className="text-xs font-bold uppercase tracking-wide">
                  Cardiovascular · Endocrine · Hepatic risk
                </span>
              </div>

              <div className="flex flex-1 flex-col p-5">
                <h3 className="font-semibold text-white group-hover:text-accent">{profile.name}</h3>
                {profile.aliases ? (
                  <p className="mt-0.5 text-xs text-slate-500">Also known as: {profile.aliases}</p>
                ) : null}

                <p className="mt-3 line-clamp-3 flex-1 text-sm text-slate-400">
                  {profile.mechanism_of_action}
                </p>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  <Pill>{profile.category}</Pill>
                  {profile.half_life ? <Pill>{profile.half_life}</Pill> : null}
                </div>

                <p className="mt-3 flex items-center gap-1.5 text-xs font-medium text-red-300">
                  <ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" />
                  Read the full risk profile
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
