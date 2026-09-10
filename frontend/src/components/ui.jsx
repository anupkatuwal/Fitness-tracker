import { AlertTriangle, Loader2 } from 'lucide-react'

export function Card({ className = '', children, ...props }) {
  return (
    <div
      className={`rounded-2xl border border-line bg-surface shadow-lg shadow-black/20 ${className}`}
      {...props}
    >
      {children}
    </div>
  )
}

export function SectionHeading({ icon: Icon, title, subtitle, actions }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="flex items-center gap-2 text-xl font-semibold text-white">
          {Icon ? <Icon className="h-5 w-5 text-accent" aria-hidden="true" /> : null}
          {title}
        </h2>
        {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
      </div>
      {actions}
    </div>
  )
}

export function Button({ variant = 'primary', className = '', children, ...props }) {
  const variants = {
    primary:
      'bg-accent-strong text-ink hover:bg-accent disabled:bg-slate-700 disabled:text-slate-400',
    ghost: 'border border-line bg-surface-2 text-slate-200 hover:border-accent hover:text-white',
    danger: 'bg-hazard text-white hover:bg-red-600',
  }
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors disabled:cursor-not-allowed ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

export function Field({ label, hint, children, htmlFor }) {
  return (
    <label className="block text-sm" htmlFor={htmlFor}>
      <span className="mb-1.5 block font-medium text-slate-300">{label}</span>
      {children}
      {hint ? <span className="mt-1 block text-xs text-slate-500">{hint}</span> : null}
    </label>
  )
}

const controlClasses =
  'w-full rounded-lg border border-line bg-surface-2 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-accent focus:outline-none'

export function Input({ className = '', ...props }) {
  return <input className={`${controlClasses} ${className}`} {...props} />
}

export function Select({ className = '', children, ...props }) {
  return (
    <select className={`${controlClasses} ${className}`} {...props}>
      {children}
    </select>
  )
}

export function Spinner({ label = 'Loading' }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-sm text-slate-400" role="status">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
      <span>{label}...</span>
    </div>
  )
}

export function ErrorNote({ children, onRetry }) {
  if (!children) return null
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 rounded-lg border border-hazard/50 bg-hazard/10 px-4 py-3 text-sm text-red-200"
    >
      <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span className="flex-1">{children}</span>
      {onRetry ? (
        <button onClick={onRetry} className="font-semibold text-red-100 underline underline-offset-2">
          Retry
        </button>
      ) : null}
    </div>
  )
}

export function EmptyState({ icon: Icon, title, children }) {
  return (
    <div className="rounded-2xl border border-dashed border-line px-6 py-12 text-center">
      {Icon ? <Icon className="mx-auto mb-3 h-8 w-8 text-slate-600" aria-hidden="true" /> : null}
      <p className="font-medium text-slate-300">{title}</p>
      {children ? <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">{children}</p> : null}
    </div>
  )
}

export function Pill({ children, className = '' }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border border-line bg-surface-2 px-2.5 py-0.5 text-xs font-medium text-slate-300 ${className}`}
    >
      {children}
    </span>
  )
}
