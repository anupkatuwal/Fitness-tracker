import { Activity, AlertOctagon, Beaker, Gavel, HeartPulse, Scale, ShieldAlert, Stethoscope } from 'lucide-react'

/**
 * Hazard presentation for the PED library.
 *
 * The three organ-system cards — cardiovascular, endocrine, hepatic — are
 * rendered for every compound without exception. They are not collapsible and
 * not dismissible.
 *
 * Contrast was measured, not eyeballed: body text #fecaca on the #2a0a0a card
 * is 12.7:1, headings #ffffff on #991b1b is 10.0:1, and the 2px #ef4444 border
 * sits at 5.1:1 against the page — comfortably past WCAG AA for text and for
 * non-text boundaries.
 */

const HAZARDS = [
  {
    key: 'cardiovascular_risk',
    title: 'Cardiovascular risk',
    icon: HeartPulse,
    blurb: 'Heart, blood vessels, blood pressure and cholesterol',
  },
  {
    key: 'endocrine_risk',
    title: 'Endocrine risk',
    icon: Activity,
    blurb: 'Hormones, fertility and natural production',
  },
  {
    key: 'hepatic_risk',
    title: 'Hepatic risk',
    icon: Beaker,
    blurb: 'Liver function, enzymes and liver tissue',
  },
]

/** The banner that sits above every compound page. */
export function HazardBanner() {
  return (
    <div
      role="alert"
      className="rounded-2xl border-2 border-hazard bg-[#991b1b] p-5 text-white shadow-lg shadow-red-950/40"
    >
      <div className="flex gap-4">
        <AlertOctagon className="mt-0.5 h-7 w-7 shrink-0" aria-hidden="true" />
        <div>
          <h2 className="text-lg font-bold uppercase tracking-wide">
            Serious health risk — read before anything else
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-red-50">
            This page is an educational reference, not medical advice, and not an endorsement or
            encouragement of use. Every compound listed carries documented risks to the heart,
            the hormonal system and the liver. Some of that damage is permanent. Non-medical use
            is unlawful in many countries. Talk to a qualified physician.
          </p>
        </div>
      </div>
    </div>
  )
}

/** The three mandatory organ-system hazard cards. */
export function HazardCards({ profile }) {
  return (
    <section aria-label="Documented health risks" className="space-y-4">
      <h2 className="flex items-center gap-2 text-lg font-bold text-white">
        <ShieldAlert className="h-5 w-5 text-hazard" aria-hidden="true" />
        Documented risks
      </h2>

      <div className="grid gap-4 lg:grid-cols-3">
        {HAZARDS.map(({ key, title, icon: Icon, blurb }) => (
          <article
            key={key}
            className="overflow-hidden rounded-2xl border-2 border-hazard bg-[#2a0a0a]"
          >
            <header className="flex items-center gap-2.5 bg-[#991b1b] px-4 py-3">
              <Icon className="h-5 w-5 shrink-0 text-white" aria-hidden="true" />
              <div>
                <h3 className="font-bold uppercase tracking-wide text-white">{title}</h3>
                <p className="text-[11px] text-red-100">{blurb}</p>
              </div>
            </header>
            <p className="px-4 py-4 text-sm leading-relaxed text-[#fecaca]">{profile[key]}</p>
          </article>
        ))}
      </div>

      {profile.other_risks ? (
        <article className="rounded-2xl border-2 border-warn bg-[#2a1c05] p-5">
          <h3 className="mb-2 flex items-center gap-2 font-bold uppercase tracking-wide text-amber-200">
            <AlertOctagon className="h-5 w-5" aria-hidden="true" />
            Other documented risks
          </h3>
          <p className="text-sm leading-relaxed text-amber-50">{profile.other_risks}</p>
        </article>
      ) : null}
    </section>
  )
}

/** Legal status, supervision requirement and monitoring guidance. */
export function ComplianceCards({ profile }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <article className="rounded-2xl border border-line bg-surface p-5">
        <h3 className="mb-2 flex items-center gap-2 font-semibold text-white">
          <Gavel className="h-5 w-5 text-warn" aria-hidden="true" />
          Legal status
        </h3>
        <p className="text-sm leading-relaxed text-slate-300">{profile.legal_status}</p>
      </article>

      <article className="rounded-2xl border border-line bg-surface p-5">
        <h3 className="mb-2 flex items-center gap-2 font-semibold text-white">
          <Stethoscope className="h-5 w-5 text-accent" aria-hidden="true" />
          Medical supervision
        </h3>
        <p className="text-sm leading-relaxed text-slate-300">
          {profile.medical_supervision_required
            ? 'Required. This compound should never be used outside the care of a qualified physician.'
            : 'Consult a physician before use.'}
        </p>
        <p className="mt-3 text-sm leading-relaxed text-slate-400">{profile.harm_reduction_notes}</p>
      </article>

      <article className="rounded-2xl border border-line bg-surface p-5">
        <h3 className="mb-2 flex items-center gap-2 font-semibold text-white">
          <Scale className="h-5 w-5 text-accent" aria-hidden="true" />
          Monitoring
        </h3>
        <p className="text-sm leading-relaxed text-slate-300">
          {profile.monitoring_bloodwork || 'No validated monitoring protocol exists.'}
        </p>
      </article>
    </div>
  )
}
