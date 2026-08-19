import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { createReport, reportDownloadUrl } from '../api/client'
import { ErrorMessage } from '../components/Feedback'

export function ReportsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const id = Number(projectId)
  const [busy, setBusy] = useState(false)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleCreate() {
    setBusy(true)
    setError(null)
    try {
      await createReport(id)
      setReady(true)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="max-w-lg space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Excel-Report</h2>
      <p className="text-sm text-slate-600">
        Erzeugt eine Excel-Datei mit Zusammenfassung, Nur-Schema-, Nur-Grundriss-
        und Abweichungs-Sheet.
      </p>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <div className="flex gap-3">
        <button
          onClick={handleCreate}
          disabled={busy}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Report wird erzeugt…' : 'Report erzeugen'}
        </button>

        <a
          href={reportDownloadUrl(id)}
          className={[
            'rounded-md border px-4 py-2 text-sm font-medium',
            ready
              ? 'border-slate-300 text-slate-700 hover:bg-slate-50'
              : 'pointer-events-none border-slate-200 text-slate-400',
          ].join(' ')}
        >
          Excel herunterladen
        </a>
      </div>
    </section>
  )
}
