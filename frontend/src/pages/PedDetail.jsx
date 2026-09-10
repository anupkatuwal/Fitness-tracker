import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, BookOpen, Microscope, Target } from 'lucide-react'
import { Card, ErrorNote, Pill, Spinner } from '../components/ui.jsx'
import { ComplianceCards, HazardBanner, HazardCards } from '../components/HazardCards.jsx'
import { api } from '../lib/api.js'

function Detail({ label, value }) {
  if (!value) return null
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-200">{value}</dd>
    </div>
  )
}

export default function PedDetail() {
  const { slug } = useParams()
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api
      .ped(slug)
      .then(setProfile)
      .catch((err) => setError(err.message || 'Could not load this compound.'))
      .finally(() => setLoading(false))
  }, [slug])

  if (loading) return <Spinner label="Loading compound" />
  if (error) return <ErrorNote>{error}</ErrorNote>
  if (!profile) return null

  return (
    <article className="space-y-8">
      <Link
        to="/peds"
        className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-accent"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to the library
      </Link>

      {/* The banner and the three hazard cards render on every compound page,
          before any of the descriptive content. */}
      <HazardBanner />

      <header>
        <h1 className="text-3xl font-bold text-white">{profile.name}</h1>
        {profile.aliases ? (
          <p className="mt-1 text-sm text-slate-500">Also known as: {profile.aliases}</p>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          <Pill>{profile.category}</Pill>
          <Pill>{profile.compound_class}</Pill>
          {profile.administration_route ? <Pill>{profile.administration_route}</Pill> : null}
        </div>
      </header>

      <HazardCards profile={profile} />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="p-6 lg:col-span-2">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
            <Microscope className="h-5 w-5 text-accent" aria-hidden="true" />
            How it works
          </h2>
          <p className="text-sm leading-relaxed text-slate-300">{profile.mechanism_of_action}</p>

          <h2 className="mb-3 mt-6 flex items-center gap-2 text-lg font-semibold text-white">
            <Target className="h-5 w-5 text-accent" aria-hidden="true" />
            Claimed effects
          </h2>
          <p className="text-sm leading-relaxed text-slate-300">{profile.claimed_effects}</p>
          <p className="mt-2 text-xs text-slate-500">
            These are the effects people seek — listing them is not a claim that they occur, are
            worth the risk, or apply to you.
          </p>

          <h2 className="mb-3 mt-6 flex items-center gap-2 text-lg font-semibold text-white">
            <BookOpen className="h-5 w-5 text-accent" aria-hidden="true" />
            What the evidence actually says
          </h2>
          <p className="text-sm leading-relaxed text-slate-300">{profile.evidence_summary}</p>
        </Card>

        <Card className="h-fit p-6">
          <h2 className="mb-4 font-semibold text-white">At a glance</h2>
          <dl className="space-y-4">
            <Detail label="Category" value={profile.category} />
            <Detail label="Compound class" value={profile.compound_class} />
            <Detail label="Route" value={profile.administration_route} />
            <Detail label="Half-life" value={profile.half_life} />
            <Detail
              label="Medical supervision"
              value={profile.medical_supervision_required ? 'Required' : 'Advised'}
            />
          </dl>
        </Card>
      </div>

      <ComplianceCards profile={profile} />

      <p className="rounded-xl border border-line bg-surface px-5 py-4 text-xs leading-relaxed text-slate-500">
        Vanguard Fitness publishes this reference so that people who are going to encounter these
        compounds encounter accurate information about their risks first. It is not medical advice,
        not a protocol, and not an endorsement. If you are considering use, the safest next step is
        a conversation with a physician — not a forum.
      </p>
    </article>
  )
}
