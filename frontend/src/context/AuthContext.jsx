import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, getToken, setToken } from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])

  // Restore the session on first load from a stored token.
  useEffect(() => {
    let cancelled = false

    async function restore() {
      if (!getToken()) {
        setLoading(false)
        return
      }
      try {
        const profile = await api.me()
        if (!cancelled) setUser(profile)
      } catch {
        if (!cancelled) logout()
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    restore()
    return () => {
      cancelled = true
    }
  }, [logout])

  // An expired token anywhere in the app ends the session cleanly.
  useEffect(() => {
    window.addEventListener('vanguard:unauthorized', logout)
    return () => window.removeEventListener('vanguard:unauthorized', logout)
  }, [logout])

  const login = useCallback(async (identifier, password) => {
    const data = await api.login(identifier, password)
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const register = useCallback(async (payload) => {
    const data = await api.register(payload)
    setToken(data.access_token)
    setUser(data.user)
    return data.user
  }, [])

  const updateProfile = useCallback(async (payload) => {
    const updated = await api.updateMe(payload)
    setUser(updated)
    return updated
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout, updateProfile }),
    [user, loading, login, register, logout, updateProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside an AuthProvider')
  return context
}
