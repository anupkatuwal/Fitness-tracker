import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { LogIn, Shield, UserPlus } from 'lucide-react'
import { Button, Card, ErrorNote, Field, Input } from '../components/ui.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { user, login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ identifier: '', email: '', username: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const redirectTo = location.state?.from?.pathname || '/macros'
  if (user) return <Navigate to={redirectTo} replace />

  const update = (key) => (event) => setForm((prev) => ({ ...prev, [key]: event.target.value }))

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      if (mode === 'login') {
        await login(form.identifier.trim(), form.password)
      } else {
        await register({
          email: form.email.trim(),
          username: form.username.trim(),
          password: form.password,
        })
      }
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-md py-8">
      <div className="mb-6 text-center">
        <Shield className="mx-auto mb-3 h-10 w-10 text-accent" aria-hidden="true" />
        <h1 className="text-2xl font-bold text-white">
          {mode === 'login' ? 'Welcome back' : 'Create your account'}
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          {mode === 'login'
            ? 'Sign in to track your macros and goals.'
            : 'Your macro log and goals are tied to your account.'}
        </p>
      </div>

      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'login' ? (
            <Field label="Email or username" htmlFor="identifier">
              <Input
                id="identifier"
                value={form.identifier}
                onChange={update('identifier')}
                autoComplete="username"
                required
              />
            </Field>
          ) : (
            <>
              <Field label="Email" htmlFor="email">
                <Input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={update('email')}
                  autoComplete="email"
                  required
                />
              </Field>
              <Field label="Username" htmlFor="username" hint="At least 3 characters.">
                <Input
                  id="username"
                  value={form.username}
                  onChange={update('username')}
                  minLength={3}
                  autoComplete="username"
                  required
                />
              </Field>
            </>
          )}

          <Field
            label="Password"
            htmlFor="password"
            hint={mode === 'register' ? 'At least 8 characters.' : undefined}
          >
            <Input
              id="password"
              type="password"
              value={form.password}
              onChange={update('password')}
              minLength={mode === 'register' ? 8 : undefined}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              required
            />
          </Field>

          <ErrorNote>{error}</ErrorNote>

          <Button type="submit" disabled={busy} className="w-full">
            {mode === 'login' ? <LogIn className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
            {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Create account'}
          </Button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-400">
          {mode === 'login' ? "Don't have an account?" : 'Already registered?'}{' '}
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login')
              setError('')
            }}
            className="font-semibold text-accent hover:underline"
          >
            {mode === 'login' ? 'Create one' : 'Sign in'}
          </button>
        </p>
      </Card>

      <p className="mt-6 text-center text-xs text-slate-500">
        The <Link to="/exercises" className="text-accent hover:underline">exercise directory</Link>,{' '}
        <Link to="/peds" className="text-accent hover:underline">PED library</Link> and{' '}
        <Link to="/calculators" className="text-accent hover:underline">calculators</Link> are open
        without an account.
      </p>
    </div>
  )
}
