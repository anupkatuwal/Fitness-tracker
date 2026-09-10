import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertTriangle, ArrowLeft, CheckCircle2, Dumbbell, ShieldCheck, XCircle } from 'lucide-react'
import { Card, ErrorNote, Pill, Spinner } from '../components/ui.jsx'
import { api } from '../lib/api.js'

/** Splits the seeded "1. ... 2. ..." block into individual steps. */
function parseSteps(text) {
  return (text || '')
    .split('\n')
    .map((line) => line.replace(/^\s*\d+\.\s*/, '').trim())
    .filter(Boolean)
}

export default function ExerciseDetail() {
  const { slug } = useParams()
  const [exercise, setExercise] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .exercise(slug)
      .then(setExercise)
      .catch((err) => setError(err.message || 'Could not load this exercise.'))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) return <Spinner label="Loading exercise" />
  if (error) return <ErrorNote>{error}</ErrorNote>
  if (!exercise) return null

  const steps = parseSteps(exercise.form_instructions)

  return (
    <article className="space-y-6">
      <Link
        to="/exercises"
        className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-accent"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to the directory
      </Link>

      <header>
        <h1 className="text-3xl font-bold text-white">{exercise.name}</h1>
        <div className="mt-3 flex flex-wrap gap-2">
          <Pill>{exercise.muscle_group}</Pill>
          <Pill>{exercise.equipment}</Pill>
          <Pill>{exercise.mechanic}</Pill>
          <Pill>{exercise.difficulty}</Pill>
        </div>
        <p className="mt-4 max-w-3xl text-slate-300">{exercise.description}</p>
        {exercise.secondary_muscles ? (
          <p className="mt-2 text-sm text-slate-500">
            <span className="font-medium text-slate-400">Also works:</span>{' '}
            {exercise.secondary_muscles}
          </p>
        ) : null}
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
            <Dumbbell className="h-5 w-5 text-accent" aria-hidden="true" />
            How to perform it
          </h2>
          <ol className="space-y-3">
            {steps.map((step, index) => (
              <li key={index} className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-strong/15 text-xs font-bold text-accent">
                  {index + 1}
                </span>
                <p className="text-sm leading-relaxed text-slate-300">{step}</p>
              </li>
            ))}
          </ol>
        </Card>

        <div className="space-y-6">
          {exercise.common_mistakes ? (
            <Card className="border-warn/40 p-6">
              <h2 className="mb-3 flex items-center gap-2 font-semibold text-warn">
                <XCircle className="h-5 w-5" aria-hidden="true" />
                Common mistakes
              </h2>
              <p className="text-sm leading-relaxed text-slate-300">{exercise.common_mistakes}</p>
            </Card>
          ) : null}

          {exercise.safety_notes ? (
            <Card className="border-hazard/50 bg-hazard/5 p-6">
              <h2 className="mb-3 flex items-center gap-2 font-semibold text-red-300">
                <AlertTriangle className="h-5 w-5" aria-hidden="true" />
                Safety
              </h2>
              <p className="text-sm leading-relaxed text-red-100/90">{exercise.safety_notes}</p>
            </Card>
          ) : null}

          <Card className="p-6">
            <h2 className="mb-3 flex items-center gap-2 font-semibold text-white">
              <ShieldCheck className="h-5 w-5 text-accent" aria-hidden="true" />
              Before you load it
            </h2>
            <ul className="space-y-2 text-sm text-slate-400">
              {[
                'Warm up the movement pattern with light sets first.',
                'Add weight only once the form above holds for every rep.',
                'Stop the set when technique breaks down, not when you fail.',
                'Sharp pain is a stop signal — muscle burn is not.',
              ].map((tip) => (
                <li key={tip} className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-accent" aria-hidden="true" />
                  {tip}
                </li>
              ))}
            </ul>
          </Card>
        </div>
      </div>
    </article>
  )
}
