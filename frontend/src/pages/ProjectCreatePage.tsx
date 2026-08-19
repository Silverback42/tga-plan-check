import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createProject } from '../api/client'
import { ErrorMessage } from '../components/Feedback'
import type { Gewerk } from '../api/types'

const GEWERKE: Gewerk[] = ['HLK', 'ELT', 'SAN']
const inputClass =
  'w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none'

export function ProjectCreatePage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [projectCode, setProjectCode] = useState('')
  const [threshold, setThreshold] = useState(85)
  const [gewerke, setGewerke] = useState<Gewerk[]>(['HLK'])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  function toggleGewerk(gewerk: Gewerk) {
    setGewerke((current) =>
      current.includes(gewerk)
        ? current.filter((g) => g !== gewerk)
        : [...current, gewerk],
    )
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const project = await createProject({
        name,
        project_code: projectCode || null,
        gewerk_scope: gewerke,
        fuzzy_threshold: threshold,
      })
      navigate(`/projects/${project.id}/uploads`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="max-w-lg space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Neues Projekt</h2>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <label className="block space-y-1">
          <span className="text-sm font-medium text-slate-700">Name</span>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={inputClass}
            placeholder="Buerogebaeude Nord"
          />
        </label>

        <label className="block space-y-1">
          <span className="text-sm font-medium text-slate-700">
            Projektnummer (optional)
          </span>
          <input
            value={projectCode}
            onChange={(e) => setProjectCode(e.target.value)}
            className={inputClass}
            placeholder="2024-042"
          />
        </label>

        <label className="block space-y-1">
          <span className="text-sm font-medium text-slate-700">
            Fuzzy-Threshold: {threshold}
          </span>
          <input
            type="range"
            min={0}
            max={100}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="w-full"
          />
        </label>

        <fieldset className="space-y-2">
          <legend className="text-sm font-medium text-slate-700">Gewerke</legend>
          <div className="flex gap-4">
            {GEWERKE.map((gewerk) => (
              <label key={gewerk} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={gewerke.includes(gewerk)}
                  onChange={() => toggleGewerk(gewerk)}
                />
                {gewerk}
              </label>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={saving || !name}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Wird angelegt…' : 'Projekt anlegen'}
        </button>
      </form>
    </section>
  )
}
