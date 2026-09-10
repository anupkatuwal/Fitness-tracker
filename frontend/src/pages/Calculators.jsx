import { useState } from 'react'
import { Calculator, Flame, Info, Save } from 'lucide-react'
import { Button, Card, ErrorNote, Field, Input, Select, SectionHeading } from '../components/ui.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { api } from '../lib/api.js'
import { SERIES, formatNumber } from '../lib/macros.js'

const ACTIVITY_OPTIONS = [
  { value: 'sedentary', label: 'Sedentary — desk job, little exercise (x1.20)' },
  { value: 'light', label: 'Light — 1-3 sessions a week (x1.375)' },
  { value: 'moderate', label: 'Moderate — 3-5 sessions a week (x1.55)' },
  { value: 'active', label: 'Active — 6-7 sessions a week (x1.725)' },
  { value: 'very_active', label: 'Very active — physical job or twice daily (x1.90)' },
]

const GOAL_OPTIONS = [
  { value: 'cut', label: 'Cut — 20% below maintenance' },
  { value: 'maintain', label: 'Maintain' },
  { value: 'bulk', label: 'Bulk — 10% above maintenance' },
]

const MACRO_TILES = [
  { key: 'protein_g', label: 'Protein', color: SERIES.protein },
  { key: 'carbs_g', label: 'Carbs', color: SERIES.carbs },
  { key: 'fats_g', label: 'Fats', color: SERIES.fats },
  { key: 'fiber_g', label: 'Fiber', color: SERIES.fiber },
]

export default function Calculators() {
  const { user, updateProfile } = useAuth()
  const [form, setForm] = useState({
    sex: user?.sex || 'male',
    age: user?.age || 28,
    height_cm: user?.height_cm || 180,
    weight_kg: user?.weight_kg || 80,
    activity_level: user?.activity_level || 'moderate',
    goal: 'maintain',
  })
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)

  const update = (key) => (event) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }))
    setSaved(false)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    setSaved(false)
    try {
      setResult(
        await api.tdee({
          sex: form.sex,
          age: Number(form.age),
          height_cm: Number(form.height_cm),
          weight_kg: Number(form.weight_kg),
          activity_level: form.activity_level,
          goal: form.goal,
        }),
      )
    } catch (err) {
      setError(err.message || 'Could not calculate. Check the values above.')
      setResult(null)
    } finally {
      setBusy(false)
    }
  }

  async function applyAsGoals() {
    if (!result) return
    setError('')
    try {
      await updateProfile({
        sex: form.sex,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        activity_level: form.activity_level,
        goal_calories: result.target_calories,
        goal_protein_g: result.protein_g,
        goal_carbs_g: result.carbs_g,
        goal_fats_g: result.fats_g,
        goal_fiber_g: result.fiber_g,
      })
      setSaved(true)
    } catch (err) {
      setError(err.message || 'Could not save these as your goals.')
    }
  }

  return (
    <div className="space-y-8">
      <SectionHeading
        icon={Calculator}
        title="BMR & TDEE Calculator"
        subtitle="Estimate your baseline burn, your daily needs, and a macro split to match."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Sex" htmlFor="sex" hint="Used by the formula's constant term.">
                <Select id="sex" value={form.sex} onChange={update('sex')}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </Select>
              </Field>
              <Field label="Age" htmlFor="age">
                <Input id="age" type="number" min="13" max="100" value={form.age} onChange={update('age')} required />
              </Field>
              <Field label="Height (cm)" htmlFor="height">
                <Input
                  id="height"
                  type="number"
                  min="1"
                  max="272"
                  step="0.5"
                  value={form.height_cm}
                  onChange={update('height_cm')}
                  required
                />
              </Field>
              <Field label="Weight (kg)" htmlFor="weight">
                <Input
                  id="weight"
                  type="number"
                  min="1"
                  max="650"
                  step="0.1"
                  value={form.weight_kg}
                  onChange={update('weight_kg')}
                  required
                />
              </Field>
            </div>

            <Field label="Activity level" htmlFor="activity">
              <Select id="activity" value={form.activity_level} onChange={update('activity_level')}>
                {ACTIVITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </Field>

            <Field label="Goal" htmlFor="goal">
              <Select id="goal" value={form.goal} onChange={update('goal')}>
                {GOAL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </Field>

            <ErrorNote>{error}</ErrorNote>

            <Button type="submit" disabled={busy} className="w-full">
              <Flame className="h-4 w-4" />
              {busy ? 'Calculating...' : 'Calculate'}
            </Button>
          </form>
        </Card>

        <div className="space-y-6">
          {result ? (
            <>
              <Card className="p-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500">BMR</p>
                    <p className="mt-1 text-3xl font-bold text-white">
                      {formatNumber(result.bmr)}
                      <span className="ml-1 text-sm font-normal text-slate-400">kcal</span>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">At complete rest.</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500">TDEE</p>
                    <p className="mt-1 text-3xl font-bold text-accent">
                      {formatNumber(result.tdee)}
                      <span className="ml-1 text-sm font-normal text-slate-400">kcal</span>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      BMR x {result.activity_multiplier} activity.
                    </p>
                  </div>
                </div>

                <div className="mt-5 rounded-xl border border-accent/40 bg-accent-strong/10 p-4">
                  <p className="text-xs uppercase tracking-wide text-accent">
                    Daily target ({form.goal})
                  </p>
                  <p className="mt-1 text-4xl font-bold text-white">
                    {formatNumber(result.target_calories)}
                    <span className="ml-1 text-base font-normal text-slate-400">kcal</span>
                  </p>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {MACRO_TILES.map((tile) => (
                    <div key={tile.key} className="rounded-lg border border-line bg-surface-2 p-3">
                      <p className="flex items-center gap-1.5 text-xs text-slate-400">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: tile.color }}
                          aria-hidden="true"
                        />
                        {tile.label}
                      </p>
                      <p className="mt-1 text-lg font-bold text-white">
                        {formatNumber(result[tile.key])}
                        <span className="text-xs font-normal text-slate-400"> g</span>
                      </p>
                    </div>
                  ))}
                </div>

                {user ? (
                  <div className="mt-5">
                    <Button variant="ghost" onClick={applyAsGoals} className="w-full">
                      <Save className="h-4 w-4" />
                      {saved ? 'Saved as your goals' : 'Use these as my daily goals'}
                    </Button>
                  </div>
                ) : (
                  <p className="mt-5 text-center text-xs text-slate-500">
                    Sign in to save these as your tracked daily goals.
                  </p>
                )}
              </Card>
            </>
          ) : (
            <Card className="flex h-full items-center justify-center p-10 text-center">
              <p className="text-sm text-slate-500">
                Fill in your details and hit Calculate to see your numbers.
              </p>
            </Card>
          )}

          <Card className="p-6">
            <h3 className="mb-2 flex items-center gap-2 font-semibold text-white">
              <Info className="h-5 w-5 text-accent" aria-hidden="true" />
              How these numbers are worked out
            </h3>
            <ul className="space-y-2 text-sm text-slate-400">
              <li>
                <span className="font-medium text-slate-300">BMR</span> uses the Mifflin-St Jeor
                equation: (10 x kg) + (6.25 x cm) - (5 x age), then +5 for men or -161 for women.
              </li>
              <li>
                <span className="font-medium text-slate-300">TDEE</span> is BMR multiplied by a
                standard activity factor.
              </li>
              <li>
                <span className="font-medium text-slate-300">Protein</span> is set at 2 g per kg of
                bodyweight, <span className="font-medium text-slate-300">fats</span> at 25% of
                calories, and carbs fill the remainder.
              </li>
              <li>
                <span className="font-medium text-slate-300">Fiber</span> follows the common 14 g per
                1,000 kcal guideline.
              </li>
            </ul>
            <p className="mt-3 text-xs text-slate-500">
              Every one of these is a population estimate, not a measurement of you. Treat the result
              as a starting point, then adjust based on how your weight actually moves over 2-3 weeks.
            </p>
          </Card>
        </div>
      </div>
    </div>
  )
}
