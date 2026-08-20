import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { useParams } from 'react-router-dom'

import { listUploads, uploadPlan } from '../api/client'
import { EmptyState, ErrorMessage, Loading } from '../components/Feedback'
import { useAsync } from '../hooks/useAsync'
import type { Gewerk, PlanType } from '../api/types'

const GEWERKE: Gewerk[] = ['HLK', 'ELT', 'SAN']
const PLAN_TYPES: { value: PlanType; label: string }[] = [
  { value: 'schema', label: 'Schema' },
  { value: 'grundriss', label: 'Grundriss' },
]

export function UploadPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const id = Number(projectId)
  const { data: uploads, loading, error, reload } = useAsync(
    () => listUploads(id),
    [id],
  )

  const [planType, setPlanType] = useState<PlanType>('schema')
  const [gewerk, setGewerk] = useState<Gewerk>('HLK')
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const onDrop = useCallback(
    async (files: File[]) => {
      setBusy(true)
      setUploadError(null)
      try {
        for (const file of files) {
          await uploadPlan(id, file, planType, gewerk)
        }
        reload()
      } catch (cause) {
        setUploadError(cause instanceof Error ? cause.message : String(cause))
      } finally {
        setBusy(false)
      }
    },
    [id, planType, gewerk, reload],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
  })

  return (
    <section className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Plaene hochladen</h2>

      <div className="flex gap-4">
        <label className="space-y-1">
          <span className="block text-sm font-medium text-slate-700">Plantyp</span>
          <select
            value={planType}
            onChange={(e) => setPlanType(e.target.value as PlanType)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {PLAN_TYPES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="space-y-1">
          <span className="block text-sm font-medium text-slate-700">Gewerk</span>
          <select
            value={gewerk}
            onChange={(e) => setGewerk(e.target.value as Gewerk)}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            {GEWERKE.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div
        {...getRootProps()}
        className={[
          'cursor-pointer rounded-md border-2 border-dashed px-6 py-12 text-center text-sm transition-colors',
          isDragActive
            ? 'border-blue-500 bg-blue-50 text-blue-700'
            : 'border-slate-300 bg-white text-slate-500 hover:border-slate-400',
        ].join(' ')}
      >
        <input {...getInputProps()} />
        {busy
          ? 'Upload laeuft…'
          : 'PDF hierher ziehen oder klicken zum Auswaehlen'}
      </div>

      {uploadError && <ErrorMessage>{uploadError}</ErrorMessage>}

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-700">
          Hochgeladene Dateien
        </h3>
        {loading && <Loading>Uploads werden geladen…</Loading>}
        {error && <ErrorMessage>{error}</ErrorMessage>}
        {uploads && uploads.length === 0 && (
          <EmptyState>Noch keine Plaene hochgeladen.</EmptyState>
        )}
        {uploads && uploads.length > 0 && (
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
        )}
      </div>
    </section>
  )
}
