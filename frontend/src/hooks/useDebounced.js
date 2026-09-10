import { useEffect, useState } from 'react'

/** Delays a rapidly changing value — used to avoid a request per keystroke. */
export function useDebounced(value, delay = 400) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}
