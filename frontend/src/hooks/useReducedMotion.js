import { useEffect, useState } from 'react'

/**
 * Tracks the user's reduced-motion preference.
 *
 * The stylesheet already neutralises CSS transitions, but Recharts animates in
 * JavaScript and ignores the media query — so chart animation has to be turned
 * off explicitly.
 */
export function useReducedMotion() {
  const [reduced, setReduced] = useState(
    () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
  )

  useEffect(() => {
    const query = window.matchMedia?.('(prefers-reduced-motion: reduce)')
    if (!query) return
    const onChange = (event) => setReduced(event.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])

  return reduced
}
