import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Dumbbell, Search, SlidersHorizontal } from 'lucide-react'
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
import { useDebounced } from '../hooks/useDebounced.js'
import { api } from '../lib/api.js'

const DIFFICULTY_STYLES = {
  beginner: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
  intermediate: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
  advanced: 'border-red-500/40 bg-red-500/10 text-red-300',
}

export default function ExerciseDirectory() {
  const [filters, setFilters] = useState({ muscle_groups: [], equipment: [], difficulties: [] })
  const [selection, setSelection] = useState({ muscle_group: 'all', equipment: 'all', difficulty: 'all' })
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search, 300)

  const [exercises, setExercises] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .exerciseFilters()
      .then(setFilters)
      .catch(() => {
        /* Filter options are a nicety — the list below still works without them. */
      })
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    setError('')

    api
      .exercises({ ...selection, search: debouncedSearch.trim() }, controller.signal)
      .then((data) => {
        setExercises(data)
        setLoading(false)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setError(err.message || 'Could not load exercises.')
        setLoading(false)
      })

    return () => controller.abort()
  }, [selection, debouncedSearch])

  const grouped = useMemo(() => {
    const groups = new Map()
    exercises.forEach((exercise) => {
      const list = groups.get(exercise.muscle_group) || []
      list.push(exercise)
      groups.set(exercise.muscle_group, list)
    })
    return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]))
  }, [exercises])

  const update = (key) => (event) => setSelection((prev) => ({ ...prev, [key]: event.target.value }))

  return (
    <div className="space-y-8">
      <SectionHeading
        icon={Dumbbell}
        title="Exercise Directory"
        subtitle="Filter by muscle group and equipment. Every entry includes step-by-step form cues."
      />

      <Card className="p-5">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-slate-300">
          <SlidersHorizontal className="h-4 w-4 text-accent" aria-hidden="true" />
          Filters
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Search" htmlFor="exercise-search">
            <div className="relative">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
                aria-hidden="true"
              />
              <Input
                id="exercise-search"
                className="pl-9"
                placeholder="Squat, row, press..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </Field>

          <Field label="Muscle group" htmlFor="muscle-group">
            <Select id="muscle-group" value={selection.muscle_group} onChange={update('muscle_group')}>
              <option value="all">All muscle groups</option>
              {filters.muscle_groups.map((group) => (
                <option key={group} value={group}>
                  {group}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Equipment" htmlFor="equipment">
            <Select id="equipment" value={selection.equipment} onChange={update('equipment')}>
              <option value="all">All equipment</option>
              {filters.equipment.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Select>
          </Field>

          <Field label="Difficulty" htmlFor="difficulty">
            <Select id="difficulty" value={selection.difficulty} onChange={update('difficulty')}>
              <option value="all">All levels</option>
              {filters.difficulties.map((level) => (
                <option key={level} value={level}>
                  {level[0].toUpperCase() + level.slice(1)}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </Card>

      <ErrorNote>{error}</ErrorNote>

      {loading ? (
        <Spinner label="Loading exercises" />
      ) : exercises.length === 0 ? (
        <EmptyState icon={Dumbbell} title="No exercises match those filters">
          Try widening the muscle group or equipment filter.
        </EmptyState>
      ) : (
        <div className="space-y-8">
          <p className="text-sm text-slate-500">
            Showing {exercises.length} exercise{exercises.length === 1 ? '' : 's'}.
          </p>
          {grouped.map(([group, items]) => (
            <section key={group}>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
                {group}
              </h3>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {items.map((exercise) => (
                  <Link
                    key={exercise.id}
                    to={`/exercises/${exercise.slug}`}
                    className="group flex h-full flex-col rounded-2xl border border-line bg-surface p-5 transition-colors hover:border-accent"
                  >
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <h4 className="font-semibold text-white group-hover:text-accent">
                        {exercise.name}
                      </h4>
                      <Pill className={DIFFICULTY_STYLES[exercise.difficulty] || ''}>
                        {exercise.difficulty}
                      </Pill>
                    </div>
                    <p className="mb-4 line-clamp-3 flex-1 text-sm text-slate-400">
                      {exercise.description}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      <Pill>{exercise.equipment}</Pill>
                      <Pill>{exercise.mechanic}</Pill>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  )
}
