import { useState } from 'react'

import { listAnlagen, startExtraction } from '../api/client'
import {
  EmptyState,
  ErrorMessage,
  InvalidProjectId,
  Loading,
} from '../components/Feedback'
import { useAsync } from '../hooks/useAsync'
import { useProjectId } from '../hooks/useProjectId'
import type { Anlage } from '../api/types'

const COLUMNS = ['Label', 'Plantyp', 'Gewerk', 'Anlagentyp', 'Raum', 'Seite']

export function ExtractionPage() {
  const projectId = useProjectId()
  if (projectId === null) {
    return <InvalidProjectId />
  }
  return <ExtractionView projectId={projectId} />
}

function ExtractionView({ projectId }: { projectId: number }) {
  const { data: anlagen, loading, error, reload } = useAsync(
    () => listAnlagen(projectId),
    [projectId],
  )
  const [actionError, setActionError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleExtract() {
    setBusy(true)
    setActionError(null)
    try {
      await startExtraction(projectId)
      reload()
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">Extrahierte Anlagen</h2>
        <button
          onClick={handleExtract}
          disabled={busy}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Extraktion laeuft…' : 'Extraktion starten'}
        </button>
      </div>

      {actionError && <ErrorMessage>{actionError}</ErrorMessage>}
      {loading && <Loading>Anlagen werden geladen…</Loading>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {anlagen?.length === 0 && (
        <EmptyState>
          Noch keine Anlagen extrahiert — bitte Extraktion starten.
        </EmptyState>
      )}
      {anlagen && anlagen.length > 0 && <AnlagenTable anlagen={anlagen} />}
    </section>
  )
}

function AnlagenTable({ anlagen }: { anlagen: Anlage[] }) {
  return (
    <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-600">
          <tr>
            {COLUMNS.map((column) => (
              <th key={column} className="px-4 py-2 font-medium">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {anlagen.map((anlage) => (
            <AnlageRow key={anlage.id} anlage={anlage} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function AnlageRow({ anlage }: { anlage: Anlage }) {
  return (
    <tr>
      <td className="px-4 py-2 font-medium text-slate-800">{anlage.label_raw}</td>
      <td className="px-4 py-2 text-slate-600">{anlage.plan_type}</td>
      <td className="px-4 py-2 text-slate-600">{anlage.gewerk}</td>
      <td className="px-4 py-2 text-slate-600">{anlage.anlagentyp ?? '—'}</td>
      <td className="px-4 py-2 text-slate-600">{anlage.room_code ?? '—'}</td>
      <td className="px-4 py-2 text-slate-600">{anlage.page ?? '—'}</td>
    </tr>
  )
}
