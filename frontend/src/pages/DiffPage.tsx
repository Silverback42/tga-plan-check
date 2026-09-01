import { useState } from 'react'

import { getDiffSummary, listDiff, startDiff, startMatching } from '../api/client'
import {
  EmptyState,
  ErrorMessage,
  InvalidProjectId,
  Loading,
} from '../components/Feedback'
import { useAsync } from '../hooks/useAsync'
import { useProjectId } from '../hooks/useProjectId'
import type { DiffEntry, DiffSummary, DiffType } from '../api/types'

const TABS: { value: DiffType; label: string }[] = [
  { value: 'only_schema', label: 'Nur Schema' },
  { value: 'only_grundriss', label: 'Nur Grundriss' },
  { value: 'attr_mismatch', label: 'Attribut-Abweichung' },
  { value: 'room_mismatch', label: 'Raum-Abweichung' },
]

const SEVERITY_CLASS: Record<string, string> = {
  error: 'bg-red-100 text-red-700',
  warning: 'bg-amber-100 text-amber-700',
  info: 'bg-slate-100 text-slate-600',
}

/** Zeigt die Detailfelder eines Diff-Eintrags kompakt als Text. */
function detailText(entry: DiffEntry): string {
  const details = entry.details_json
  if (details.schema_wert !== undefined) {
    return `${details.schema_wert} → ${details.grundriss_wert}`
  }
  return String(details.label_raw ?? '—')
}

export function DiffPage() {
  const projectId = useProjectId()
  if (projectId === null) {
    return <InvalidProjectId />
  }
  return <DiffView projectId={projectId} />
}

function DiffView({ projectId }: { projectId: number }) {
  const [tab, setTab] = useState<DiffType>('only_schema')
  const [runs, setRuns] = useState(0)
  const summary = useAsync(() => getDiffSummary(projectId), [projectId, runs])
  const { data: entries, loading, error } = useAsync(
    () => listDiff(projectId, tab),
    [projectId, tab, runs],
  )

  return (
    <section className="space-y-6">
      <DiffToolbar
        projectId={projectId}
        onFinished={() => setRuns((value) => value + 1)}
      />
      {summary.data && <SummaryCards summary={summary.data} />}
      <TabBar active={tab} onSelect={setTab} />

      {loading && <Loading>Eintraege werden geladen…</Loading>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {entries?.length === 0 && (
        <EmptyState>Keine Eintraege in dieser Kategorie.</EmptyState>
      )}
      {entries && entries.length > 0 && <DiffList entries={entries} />}
    </section>
  )
}

interface ToolbarProps {
  projectId: number
  onFinished: () => void
}

function DiffToolbar({ projectId, onFinished }: ToolbarProps) {
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  async function handleRun() {
    setBusy(true)
    setActionError(null)
    try {
      await startMatching(projectId)
      await startDiff(projectId)
      onFinished()
    } catch (cause) {
      setActionError(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">Abgleich</h2>
        <button
          onClick={handleRun}
          disabled={busy}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Abgleich laeuft…' : 'Matching + Diff starten'}
        </button>
      </div>
      {actionError && <ErrorMessage>{actionError}</ErrorMessage>}
    </>
  )
}

function SummaryCards({ summary }: { summary: DiffSummary }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {TABS.map((item) => (
        <div
          key={item.value}
          className="rounded-md border border-slate-200 bg-white px-4 py-3"
        >
          <p className="text-xs uppercase tracking-wide text-slate-500">
            {item.label}
          </p>
          <p className="text-2xl font-semibold text-slate-800">
            {summary[item.value] ?? 0}
          </p>
        </div>
      ))}
    </div>
  )
}

interface TabBarProps {
  active: DiffType
  onSelect: (value: DiffType) => void
}

function TabBar({ active, onSelect }: TabBarProps) {
  return (
    <div className="flex gap-1 border-b border-slate-200">
      {TABS.map((item) => (
        <button
          key={item.value}
          onClick={() => onSelect(item.value)}
          aria-current={active === item.value ? 'page' : undefined}
          className={[
            'px-4 py-2 text-sm transition-colors',
            active === item.value
              ? 'border-b-2 border-blue-600 font-medium text-blue-700'
              : 'text-slate-500 hover:text-slate-700',
          ].join(' ')}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}

function DiffList({ entries }: { entries: DiffEntry[] }) {
  return (
    <ul className="divide-y divide-slate-200 rounded-md border border-slate-200 bg-white">
      {entries.map((entry) => (
        <li
          key={entry.id}
          className="flex items-center justify-between px-4 py-3 text-sm"
        >
          <span className="text-slate-800">{detailText(entry)}</span>
          <span
            className={[
              'rounded-full px-2 py-0.5 text-xs font-medium',
              SEVERITY_CLASS[entry.severity] ?? SEVERITY_CLASS.info,
            ].join(' ')}
          >
            {entry.severity}
          </span>
        </li>
      ))}
    </ul>
  )
}
