import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight,
  Calculator,
  Dumbbell,
  FlaskConical,
  LayoutDashboard,
  Shield,
  Utensils,
} from 'lucide-react'
import { Card, ErrorNote, SectionHeading, Spinner } from '../components/ui.jsx'
import { MacroProgressBars, MacroTrendChart } from '../components/charts.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { api } from '../lib/api.js'
import { formatNumber } from '../lib/macros.js'

const FEATURES = [
  {
    to: '/macros',
    icon: Utensils,
    title: 'Macro Tracker',
    body: 'Search real products from the OpenFoodFacts database, log what you ate, and track the week.',
  },
  {
    to: '/exercises',
    icon: Dumbbell,
    title: 'Exercise Directory',
    body: 'Filter by muscle group and equipment, with step-by-step form cues and the mistakes to avoid.',
  },
  {
    to: '/peds',
    icon: FlaskConical,
    title: 'PED & Peptide Library',
    body: 'An honest educational reference — mechanism, evidence, and the documented risks to your heart, hormones and liver.',
  },
  {
    to: '/calculators',
    icon: Calculator,
    title: 'BMR & TDEE Calculator',
    body: 'Estimate your baseline burn and daily needs, then apply the result as your tracked goals.',
  },
]

function Hero() {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-line bg-gradient-to-br from-accent-strong/15 to-transparent px-6 py-10 sm:px-10">
        <Shield className="mb-4 h-10 w-10 text-accent" aria-hidden="true" />
        <h1 className="text-3xl font-bold text-white sm:text-4xl">
          Train informed. <span className="text-accent">Track everything.</span>
        </h1>
        <p className="mt-3 max-w-2xl text-slate-300">
          Vanguard Fitness puts your macros, your lifts and a straight-talking compound reference in
          one place. No hype, no protocols to sell you — just the numbers and the evidence.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 rounded-lg bg-accent-strong px-5 py-2.5 text-sm font-semibold text-ink hover:bg-accent"
          >
            Get started
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <Link
            to="/exercises"
            className="inline-flex items-center gap-2 rounded-lg border border-line px-5 py-2.5 text-sm font-semibold text-slate-200 hover:border-accent hover:text-white"
          >
            Browse exercises
          </Link>
        </div>
      </div>
    </Card>
  )
}

function FeatureGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {FEATURES.map((feature) => {
        const Icon = feature.icon
        return (
          <Link
            key={feature.to}
            to={feature.to}
            className="group rounded-2xl border border-line bg-surface p-6 transition-colors hover:border-accent"
          >
            <Icon className="mb-3 h-6 w-6 text-accent" aria-hidden="true" />
            <h3 className="font-semibold text-white group-hover:text-accent">{feature.title}</h3>
            <p className="mt-1.5 text-sm text-slate-400">{feature.body}</p>
          </Link>
        )
      })}
    </div>
  )
}

export default function Dashboard() {
  const { user, loading: authLoading } = useAuth()
  const [summary, setSummary] = useState(null)
  const [trend, setTrend] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) {
      setSummary(null)
      setTrend(null)
      return
    }

    let cancelled = false
    setLoading(true)
    setError('')

    Promise.all([api.summary(), api.trend(7)])
      .then(([summaryData, trendData]) => {
        if (cancelled) return
        setSummary(summaryData)
        setTrend(trendData)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Could not load your dashboard data.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [user])

  if (authLoading) return <Spinner label="Loading" />

  if (!user) {
    return (
      <div className="space-y-8">
        <Hero />
        <FeatureGrid />
      </div>
    )
  }

  const remaining = Math.max(
    (summary?.goals?.calories || 0) - (summary?.totals?.calories || 0),
    0,
  )

  return (
    <div className="space-y-8">
      <SectionHeading
        icon={LayoutDashboard}
        title={`Welcome back, ${user.full_name || user.username}`}
        subtitle="Here is where today stands."
      />

      <ErrorNote>{error}</ErrorNote>

      {loading ? (
        <Spinner label="Loading today" />
      ) : (
        <>
          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="p-6 lg:col-span-2">
              <h3 className="mb-4 font-semibold text-white">Today against your goals</h3>
              <MacroProgressBars totals={summary?.totals} goals={summary?.goals} />
            </Card>

            <div className="space-y-6">
              <Card className="p-6">
                <p className="text-xs uppercase tracking-wide text-slate-500">Calories left today</p>
                <p className="mt-1 text-4xl font-bold text-accent">
                  {formatNumber(remaining)}
                  <span className="ml-1 text-base font-normal text-slate-400">kcal</span>
                </p>
                <p className="mt-2 text-sm text-slate-400">
                  {formatNumber(summary?.totals?.calories || 0)} of{' '}
                  {formatNumber(summary?.goals?.calories || 0)} eaten ·{' '}
                  {summary?.entries?.length || 0} entries logged.
                </p>
                <Link
                  to="/macros"
                  className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-accent hover:underline"
                >
                  Log a food
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Link>
              </Card>
            </div>
          </div>

          <MacroTrendChart trend={trend} days={7} />
        </>
      )}

      <FeatureGrid />
    </div>
  )
}
