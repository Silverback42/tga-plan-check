import { useState } from 'react'

import { createReport, reportDownloadUrl } from '../api/client'
import { ErrorMessage, InvalidProjectId } from '../components/Feedback'
import { useProjectId } from '../hooks/useProjectId'

const buttonClass =
  'rounded-md border px-4 py-2 text-sm font-medium'

export function ReportsPage() {
  const projectId = useProjectId()
  if (projectId === null) {
    return <InvalidProjectId />
  }
  return <ReportsView projectId={projectId} />
}

function ReportsView({ projectId }: { projectId: number }) {
  const [busy, setBusy] = useState(false)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleCreate() {
    setBusy(true)
    setError(null)
    try {
      await createReport(projectId)
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

        <DownloadLink projectId={projectId} ready={ready} />
      </div>
    </section>
  )
}

/**
 * Ohne fertigen Report wird bewusst kein <a href> gerendert: ein Link mit
 * pointer-events-none bliebe per Tastatur weiterhin aktivierbar.
 */
function DownloadLink({ projectId, ready }: { projectId: number; ready: boolean }) {
  if (!ready) {
    return (
      <span
        aria-disabled="true"
        className={`${buttonClass} border-slate-200 text-slate-400`}
      >
        Excel herunterladen
      </span>
    )
  }

  return (
    <a
      href={reportDownloadUrl(projectId)}
      className={`${buttonClass} border-slate-300 text-slate-700 hover:bg-slate-50`}
    >
      Excel herunterladen
    </a>
  )
}
