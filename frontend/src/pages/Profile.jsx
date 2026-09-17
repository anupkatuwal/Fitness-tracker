import { useState } from 'react'
import { Save, User } from 'lucide-react'
import { Button, Card, ErrorNote, Field, Input, SectionHeading, Select } from '../components/ui.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { MACRO_ROWS } from '../lib/macros.js'

const GOAL_FIELDS = MACRO_ROWS.map((row) => ({
  key: `goal_${row.key}`,
  label: `${row.label} goal`,
  unit: row.unit,
}))

export default function Profile() {
  const { user, updateProfile } = useAuth()
  const [form, setForm] = useState(() => ({
    age: user.age ?? '',
    sex: user.sex ?? 'male',
    height_cm: user.height_cm ?? '',
    weight_kg: user.weight_kg ?? '',
    activity_level: user.activity_level ?? 'moderate',
    goal_calories: user.goal_calories,
    goal_protein_g: user.goal_protein_g,
    goal_carbs_g: user.goal_carbs_g,
    goal_fats_g: user.goal_fats_g,
    goal_fiber_g: user.goal_fiber_g,
  }))
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const update = (key) => (event) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }))
    setStatus('')
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      // Blank optional fields are omitted rather than sent as empty strings.
      const payload = Object.fromEntries(
        Object.entries(form)
          .filter(([, value]) => value !== '' && value !== null)
          .map(([key, value]) => [key, key === 'sex' || key === 'activity_level' ? value : Number(value)]),
      )
      await updateProfile(payload)
      setStatus('Saved.')
    } catch (err) {
      setError(err.message || 'Could not save your profile.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <SectionHeading
        icon={User}
        title="Your profile"
        subtitle={`Signed in as ${user.email}`}
      />

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
              Body metrics
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Field label="Age" htmlFor="p-age">
                <Input id="p-age" type="number" min="13" max="100" value={form.age} onChange={update('age')} />
              </Field>
              <Field label="Sex" htmlFor="p-sex">
                <Select id="p-sex" value={form.sex} onChange={update('sex')}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </Select>
              </Field>
              <Field label="Activity level" htmlFor="p-activity">
                <Select id="p-activity" value={form.activity_level} onChange={update('activity_level')}>
                  {['sedentary', 'light', 'moderate', 'active', 'very_active'].map((level) => (
                    <option key={level} value={level}>
                      {level.replace('_', ' ')}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Height (cm)" htmlFor="p-height">
                <Input
                  id="p-height"
                  type="number"
                  min="1"
                  max="272"
                  step="0.5"
                  value={form.height_cm}
                  onChange={update('height_cm')}
                />
              </Field>
              <Field label="Weight (kg)" htmlFor="p-weight">
                <Input
                  id="p-weight"
                  type="number"
                  min="1"
                  max="650"
                  step="0.1"
                  value={form.weight_kg}
                  onChange={update('weight_kg')}
                />
              </Field>
            </div>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
              Daily macro goals
            </h3>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {GOAL_FIELDS.map((field) => (
                <Field key={field.key} label={`${field.label} (${field.unit})`} htmlFor={field.key}>
                  <Input
                    id={field.key}
                    type="number"
                    min="0"
                    step="1"
                    value={form[field.key]}
                    onChange={update(field.key)}
                  />
                </Field>
              ))}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Not sure what to put here? Run the{' '}
              <a href="/calculators" className="text-accent hover:underline">
                TDEE calculator
              </a>{' '}
              and apply its result.
            </p>
          </div>

          <ErrorNote>{error}</ErrorNote>

          <div className="flex items-center gap-3">
            <Button type="submit" disabled={busy}>
              <Save className="h-4 w-4" />
              {busy ? 'Saving...' : 'Save changes'}
            </Button>
            {status ? <span className="text-sm text-emerald-400">{status}</span> : null}
          </div>
        </form>
      </Card>
    </div>
  )
}
