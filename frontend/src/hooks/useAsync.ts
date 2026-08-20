import { useCallback, useEffect, useState } from 'react'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
}

/** Laedt Daten und haelt Lade-/Fehlerzustand — vermeidet try-catch in jeder Page. */
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  // loader wechselt bei jedem Render; deps steuern bewusst, wann neu geladen wird
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const run = useCallback(loader, deps)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    run()
      .then((result) => {
        if (active) setData(result)
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : String(cause))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    // Verhindert setState nach Unmount bzw. bei veralteten Antworten
    return () => {
      active = false
    }
  }, [run, tick])

  const reload = useCallback(() => setTick((value) => value + 1), [])
  return { data, loading, error, reload }
}
