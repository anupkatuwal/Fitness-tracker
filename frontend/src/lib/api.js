/**
 * Thin fetch wrapper around the Vanguard Fitness API.
 *
 * The JWT is held in localStorage and attached to every request. A 401 clears
 * it and dispatches `vanguard:unauthorized`, which AuthProvider listens for so
 * an expired token logs the user out instead of leaving the UI half-broken.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
const TOKEN_KEY = 'vanguard.token'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* Storage can be unavailable (private mode); the session still works. */
  }
}

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

/** FastAPI returns validation errors as a list of objects; flatten to a string. */
function readDetail(payload, fallback) {
  const detail = payload?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : null
        return field ? `${field}: ${item.msg}` : item.msg
      })
      .filter(Boolean)
      .join(', ')
  }
  return fallback
}

async function request(path, { method = 'GET', body, form, signal, auth = true } = {}) {
  const headers = {}
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let payloadBody
  if (form) {
    payloadBody = new URLSearchParams(form).toString()
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
  } else if (body !== undefined) {
    payloadBody = JSON.stringify(body)
    headers['Content-Type'] = 'application/json'
  }

  let response
  try {
    response = await fetch(`${API_BASE}${path}`, { method, headers, body: payloadBody, signal })
  } catch (error) {
    if (error?.name === 'AbortError') throw error
    throw new ApiError('Cannot reach the server. Is the backend running?', 0, null)
  }

  if (response.status === 204) return null

  let payload = null
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    payload = await response.json().catch(() => null)
  }

  if (!response.ok) {
    if (response.status === 401 && auth) {
      setToken(null)
      window.dispatchEvent(new CustomEvent('vanguard:unauthorized'))
    }
    throw new ApiError(
      readDetail(payload, `Request failed (${response.status})`),
      response.status,
      payload,
    )
  }

  return payload
}

const query = (params) => {
  const search = new URLSearchParams()
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value)
  })
  const string = search.toString()
  return string ? `?${string}` : ''
}

export const api = {
  // auth
  register: (data) => request('/auth/register', { method: 'POST', body: data, auth: false }),
  login: (username, password) =>
    request('/auth/login', { method: 'POST', form: { username, password }, auth: false }),
  me: () => request('/auth/me'),
  updateMe: (data) => request('/auth/me', { method: 'PATCH', body: data }),

  // exercises
  exercises: (filters, signal) => request(`/exercises${query(filters)}`, { signal, auth: false }),
  exerciseFilters: () => request('/exercises/filters', { auth: false }),
  exercise: (slug) => request(`/exercises/${slug}`, { auth: false }),

  // peds
  peds: (filters, signal) => request(`/peds${query(filters)}`, { signal, auth: false }),
  pedCategories: () => request('/peds/categories', { auth: false }),
  ped: (slug) => request(`/peds/${slug}`, { auth: false }),
  pedDisclaimer: () => request('/peds/disclaimer', { auth: false }),

  // macros
  searchFoods: (q, signal) => request(`/macros/search${query({ q })}`, { signal }),
  lookupBarcode: (barcode) => request(`/macros/barcode/${barcode}`),
  createLog: (data) => request('/macros/logs', { method: 'POST', body: data }),
  logs: (day) => request(`/macros/logs${query({ day })}`),
  deleteLog: (id) => request(`/macros/logs/${id}`, { method: 'DELETE' }),
  summary: (day) => request(`/macros/summary${query({ day })}`),
  trend: (days = 7) => request(`/macros/trend${query({ days })}`),

  // calculators
  tdee: (data) => request('/calculators/tdee', { method: 'POST', body: data, auth: false }),
}
