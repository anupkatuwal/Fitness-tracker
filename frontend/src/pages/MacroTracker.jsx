import { useCallback, useEffect, useState } from 'react'
import { Plus, Search, Trash2, Utensils, X } from 'lucide-react'
import {
  Button,
  Card,
  EmptyState,
  ErrorNote,
  Field,
  Input,
  Select,
  SectionHeading,
  Spinner,
  Pill,
} from '../components/ui.jsx'
import { MacroProgressBars, MacroSplitChart, MacroTrendChart } from '../components/charts.jsx'
import { useDebounced } from '../hooks/useDebounced.js'
import { api } from '../lib/api.js'
import { MEAL_TYPES, formatNumber, scaleFood, toISODate } from '../lib/macros.js'

const TREND_DAYS = 7

/** The panel that appears once a search result is picked. */
function LogFoodForm({ food, onCancel, onSaved }) {
  const [grams, setGrams] = useState(food.serving_size_g || 100)
  const [servings, setServings] = useState(1)
  const [mealType, setMealType] = useState('other')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const scaled = scaleFood(food, grams, servings)
  const totalGrams = (Number(grams) || 0) * (Number(servings) || 0)

  async function handleSave() {
    setBusy(true)
    setError('')
    try {
      await onSaved({
        food_name: food.name,
        brand: food.brand,
        barcode: food.barcode,
        source: 'openfoodfacts',
        serving_size_g: Number(grams),
        servings: Number(servings),
        meal_type: mealType,
        ...scaled,
      })
    } catch (err) {
      setError(err.message || 'Could not save this entry.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card className="border-accent/40 p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-white">{food.name}</h3>
          {food.brand ? <p className="text-sm text-slate-400">{food.brand}</p> : null}
          <p className="mt-1 text-xs text-slate-500">
            Values from OpenFoodFacts, per 100 g: {formatNumber(food.calories_per_100g, 0)} kcal ·{' '}
            {formatNumber(food.protein_per_100g, 1)}P · {formatNumber(food.carbs_per_100g, 1)}C ·{' '}
            {formatNumber(food.fats_per_100g, 1)}F
          </p>
        </div>
        <button onClick={onCancel} aria-label="Cancel" className="text-slate-500 hover:text-white">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Field label="Serving size (g)" htmlFor="grams">
          <Input
            id="grams"
            type="number"
            min="1"
            step="1"
            value={grams}
            onChange={(event) => setGrams(event.target.value)}
          />
        </Field>
        <Field label="Servings" htmlFor="servings">
          <Input
            id="servings"
            type="number"
            min="0.25"
            step="0.25"
            value={servings}
            onChange={(event) => setServings(event.target.value)}
          />
        </Field>
        <Field label="Meal" htmlFor="meal">
          <Select id="meal" value={mealType} onChange={(event) => setMealType(event.target.value)}>
            {MEAL_TYPES.map((meal) => (
              <option key={meal} value={meal}>
                {meal[0].toUpperCase() + meal.slice(1)}
              </option>
            ))}
          </Select>
        </Field>
      </div>

      <div className="mt-4 rounded-lg border border-line bg-surface-2 p-4">
        <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">
          This adds ({formatNumber(totalGrams, 0)} g total)
        </p>
        <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-5">
          {[
            ['Calories', scaled.calories, 'kcal'],
            ['Protein', scaled.protein_g, 'g'],
            ['Carbs', scaled.carbs_g, 'g'],
            ['Fats', scaled.fats_g, 'g'],
            ['Fiber', scaled.fiber_g, 'g'],
          ].map(([label, value, unit]) => (
            <div key={label}>
              <p className="text-slate-500">{label}</p>
              <p className="font-semibold text-white">
                {formatNumber(value, 1)} <span className="text-xs font-normal text-slate-400">{unit}</span>
              </p>
            </div>
          ))}
        </div>
      </div>

      <ErrorNote>{error}</ErrorNote>

      <div className="mt-4 flex gap-2">
        <Button onClick={handleSave} disabled={busy || totalGrams <= 0}>
          <Plus className="h-4 w-4" />
          {busy ? 'Saving...' : 'Add to log'}
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </Card>
  )
}

export default function MacroTracker() {
  const [day, setDay] = useState(toISODate())
  const [summary, setSummary] = useState(null)
  const [trend, setTrend] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [term, setTerm] = useState('')
  const debouncedTerm = useDebounced(term, 450)
  const [results, setResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [selected, setSelected] = useState(null)

  const refresh = useCallback(async () => {
    setLoadError('')
    try {
      const [summaryData, trendData] = await Promise.all([api.summary(day), api.trend(TREND_DAYS)])
      setSummary(summaryData)
      setTrend(trendData)
    } catch (err) {
      setLoadError(err.message || 'Could not load your macro data.')
    } finally {
      setLoading(false)
    }
  }, [day])

  useEffect(() => {
    setLoading(true)
    refresh()
  }, [refresh])

  // Live search against the backend's OpenFoodFacts route.
  useEffect(() => {
    const query = debouncedTerm.trim()
    if (query.length < 2) {
      setResults([])
      setSearchError('')
      setSearching(false)
      return
    }

    const controller = new AbortController()
    setSearching(true)
    setSearchError('')

    api
      .searchFoods(query, controller.signal)
      .then((data) => {
        setResults(data.results || [])
        setSearching(false)
      })
      .catch((err) => {
        if (err.name === 'AbortError') return
        setSearchError(err.message || 'Search failed.')
        setResults([])
        setSearching(false)
      })

    return () => controller.abort()
  }, [debouncedTerm])

  async function handleSaved(payload) {
    await api.createLog({ ...payload, logged_on: day })
    setSelected(null)
    setTerm('')
    setResults([])
    await refresh()
  }

  async function handleDelete(id) {
    await api.deleteLog(id)
    await refresh()
  }

  if (loading) return <Spinner label="Loading your macros" />

  return (
    <div className="space-y-8">
      <SectionHeading
        icon={Utensils}
        title="Macro Tracker"
        subtitle="Search real foods, log what you ate, and watch the week take shape."
        actions={
          <Field label="Date" htmlFor="day">
            <Input
              id="day"
              type="date"
              value={day}
              max={toISODate()}
              onChange={(event) => setDay(event.target.value)}
            />
          </Field>
        }
      />

      <ErrorNote onRetry={refresh}>{loadError}</ErrorNote>

      {/* ---------------------------------------------------------------- search */}
      <Card className="p-5">
        <Field label="Search foods" htmlFor="food-search" hint="Powered by the OpenFoodFacts database.">
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500"
              aria-hidden="true"
            />
            <Input
              id="food-search"
              className="pl-9"
              placeholder="e.g. greek yogurt, rolled oats, chicken breast"
              value={term}
              onChange={(event) => setTerm(event.target.value)}
              autoComplete="off"
            />
          </div>
        </Field>

        <div className="mt-4">
          {searching ? <Spinner label="Searching OpenFoodFacts" /> : null}
          <ErrorNote>{searchError}</ErrorNote>

          {!searching && !searchError && debouncedTerm.trim().length >= 2 && results.length === 0 ? (
            <p className="py-4 text-sm text-slate-500">
              No products with usable nutrition data matched &ldquo;{debouncedTerm}&rdquo;.
            </p>
          ) : null}

          {!searching && results.length > 0 ? (
            <ul className="max-h-80 space-y-2 overflow-y-auto pr-1">
              {results.map((food, index) => (
                <li key={`${food.barcode || food.name}-${index}`}>
                  <button
                    onClick={() => setSelected(food)}
                    className="flex w-full items-center gap-3 rounded-lg border border-line bg-surface-2 p-3 text-left transition-colors hover:border-accent"
                  >
                    {food.image_url ? (
                      <img
                        src={food.image_url}
                        alt=""
                        loading="lazy"
                        className="h-10 w-10 shrink-0 rounded object-cover"
                      />
                    ) : (
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-surface text-slate-600">
                        <Utensils className="h-4 w-4" aria-hidden="true" />
                      </span>
                    )}
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium text-white">{food.name}</span>
                      <span className="block truncate text-xs text-slate-500">
                        {food.brand || 'Unbranded'} · per 100 g:{' '}
                        {formatNumber(food.calories_per_100g, 0)} kcal ·{' '}
                        {formatNumber(food.protein_per_100g, 1)}P{' '}
                        {formatNumber(food.carbs_per_100g, 1)}C {formatNumber(food.fats_per_100g, 1)}F
                      </span>
                    </span>
                    <Plus className="h-4 w-4 shrink-0 text-accent" aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </Card>

      {selected ? (
        <LogFoodForm food={selected} onCancel={() => setSelected(null)} onSaved={handleSaved} />
      ) : null}

      {/* --------------------------------------------------------------- charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="mb-4 font-semibold text-white">Today against your goals</h3>
          <MacroProgressBars totals={summary?.totals} goals={summary?.goals} />
        </Card>
        <Card className="p-5">
          <h3 className="mb-4 font-semibold text-white">Macro split</h3>
          <MacroSplitChart totals={summary?.totals} />
        </Card>
      </div>

      <MacroTrendChart trend={trend} days={TREND_DAYS} />

      {/* ----------------------------------------------------------------- log */}
      <div>
        <SectionHeading title="Logged today" subtitle={`${summary?.entries?.length || 0} entries`} />
        {summary?.entries?.length ? (
          <Card className="divide-y divide-line">
            {summary.entries.map((entry) => (
              <div key={entry.id} className="flex items-center gap-3 p-4">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-white">{entry.food_name}</p>
                  <p className="truncate text-xs text-slate-500">
                    {entry.brand ? `${entry.brand} · ` : ''}
                    {formatNumber(entry.serving_size_g * entry.servings, 0)} g ·{' '}
                    {formatNumber(entry.calories, 0)} kcal · {formatNumber(entry.protein_g, 1)}P{' '}
                    {formatNumber(entry.carbs_g, 1)}C {formatNumber(entry.fats_g, 1)}F{' '}
                    {formatNumber(entry.fiber_g, 1)}Fib
                  </p>
                </div>
                <Pill>{entry.meal_type}</Pill>
                <button
                  onClick={() => handleDelete(entry.id)}
                  aria-label={`Delete ${entry.food_name}`}
                  className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-hazard/10 hover:text-hazard"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </Card>
        ) : (
          <EmptyState icon={Utensils} title="Nothing logged for this day">
            Search for a food above to add your first entry.
          </EmptyState>
        )}
      </div>
    </div>
  )
}
