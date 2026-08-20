import { useCallback, useRef, useState } from 'react'
import { useDropzone } from 'react-dropzone'

import { listUploads, uploadPlan } from '../api/client'
import {
  EmptyState,
  ErrorMessage,
  InvalidProjectId,
  Loading,
} from '../components/Feedback'
import { useAsync } from '../hooks/useAsync'
import { useProjectId } from '../hooks/useProjectId'
import type { Gewerk, PlanType, Upload } from '../api/types'

const TRADES: Gewerk[] = ['HLK', 'ELT', 'SAN']
const PLAN_TYPES: { value: PlanType; label: string }[] = [
  { value: 'schema', label: 'Schema' },
  { value: 'grundriss', label: 'Grundriss' },
]
const selectClass = 'rounded-md border border-slate-300 px-3 py-2 text-sm'

export function UploadPage() {
  const projectId = useProjectId()
  if (projectId === null) {
    return <InvalidProjectId />
  }
  return <UploadView projectId={projectId} />
}

function UploadView({ projectId }: { projectId: number }) {
  const { data: uploads, loading, error, reload } = useAsync(
    () => listUploads(projectId),
    [projectId],
  )
  const [planType, setPlanType] = useState<PlanType>('schema')
  const [trade, setTrade] = useState<Gewerk>('HLK')
  const upload = useUploadBatch(projectId, planType, trade, reload)

  return (
    <section className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Plaene hochladen</h2>
      <div className="flex gap-4">
        <PlanTypeSelect value={planType} onChange={setPlanType} />
        <TradeSelect value={trade} onChange={setTrade} />
      </div>
      <UploadDropzone onDrop={upload.onDrop} busy={upload.busy} />
      {upload.error && <ErrorMessage>{upload.error}</ErrorMessage>}
      <UploadList uploads={uploads} loading={loading} error={error} />
    </section>
  )
}

/** Laedt alle Dateien eines Drops nacheinander hoch. */
async function uploadAll(
  projectId: number,
  files: File[],
  planType: PlanType,
  trade: Gewerk,
) {
  for (const file of files) {
    await uploadPlan(projectId, file, planType, trade)
  }
}

/** Kapselt Upload-Lauf inkl. Sperre gegen parallele Drops. */
function useUploadBatch(
  projectId: number,
  planType: PlanType,
  trade: Gewerk,
  reload: () => void,
) {
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const inFlight = useRef(false)

  const onDrop = useCallback(
    async (files: File[]) => {
      // Ref statt State: der Wert muss schon im selben Tick aktuell sein
      if (inFlight.current) return
      inFlight.current = true
      setBusy(true)
      setError(null)
      try {
        await uploadAll(projectId, files, planType, trade)
        reload()
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : String(cause))
      } finally {
        inFlight.current = false
        setBusy(false)
      }
    },
    [projectId, planType, trade, reload],
  )

  return { onDrop, busy, error }
}

const DROPZONE_BASE =
  'rounded-md border-2 border-dashed px-6 py-12 text-center text-sm transition-colors'

/** Waehlt die Optik der Ablageflaeche je nach Sperr- und Drag-Zustand. */
function dropzoneClass(busy: boolean, isDragActive: boolean): string {
  if (busy) {
    return `${DROPZONE_BASE} cursor-not-allowed border-slate-200 bg-white text-slate-400`
  }
  if (isDragActive) {
    return `${DROPZONE_BASE} cursor-pointer border-blue-500 bg-blue-50 text-blue-700`
  }
  return `${DROPZONE_BASE} cursor-pointer border-slate-300 bg-white text-slate-500 hover:border-slate-400`
}

interface DropzoneProps {
  onDrop: (files: File[]) => void
  busy: boolean
}

function UploadDropzone({ onDrop, busy }: DropzoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    disabled: busy,
  })

  return (
    <div {...getRootProps()} className={dropzoneClass(busy, isDragActive)}>
      <input {...getInputProps()} />
      {busy ? 'Upload laeuft…' : 'PDF hierher ziehen oder klicken zum Auswaehlen'}
    </div>
  )
}

interface PlanTypeSelectProps {
  value: PlanType
  onChange: (value: PlanType) => void
}

function PlanTypeSelect({ value, onChange }: PlanTypeSelectProps) {
  return (
    <label className="space-y-1">
      <span className="block text-sm font-medium text-slate-700">Plantyp</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as PlanType)}
        className={selectClass}
      >
        {PLAN_TYPES.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}

interface TradeSelectProps {
  value: Gewerk
  onChange: (value: Gewerk) => void
}

function TradeSelect({ value, onChange }: TradeSelectProps) {
  return (
    <label className="space-y-1">
      <span className="block text-sm font-medium text-slate-700">Gewerk</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as Gewerk)}
        className={selectClass}
      >
        {TRADES.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}

interface UploadListProps {
  uploads: Upload[] | null
  loading: boolean
  error: string | null
}

function UploadList({ uploads, loading, error }: UploadListProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-700">
        Hochgeladene Dateien
      </h3>
      {loading && <Loading>Uploads werden geladen…</Loading>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {uploads?.length === 0 && (
        <EmptyState>Noch keine Plaene hochgeladen.</EmptyState>
      )}
      {uploads && uploads.length > 0 && <UploadRows uploads={uploads} />}
    </div>
  )
}

function UploadRows({ uploads }: { uploads: Upload[] }) {
  return (
    <ul className="divide-y divide-slate-200 rounded-md border border-slate-200 bg-white">
      {uploads.map((upload) => (
        <li
          key={upload.id}
          className="flex items-center justify-between px-4 py-2 text-sm"
        >
          <span className="text-slate-800">{upload.filename}</span>
          <span className="text-slate-500">
            {upload.plan_type} · {upload.gewerk}
          </span>
        </li>
      ))}
    </ul>
  )
}
