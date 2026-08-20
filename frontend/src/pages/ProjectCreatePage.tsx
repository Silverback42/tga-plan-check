import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createProject } from '../api/client'
import { ErrorMessage } from '../components/Feedback'
import type { Gewerk } from '../api/types'

const TRADES: Gewerk[] = ['HLK', 'ELT', 'SAN']
const inputClass =
  'w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none'
const labelClass = 'text-sm font-medium text-slate-700'

export function ProjectCreatePage() {
  const form = useProjectForm()

  return (
    <section className="max-w-lg space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Neues Projekt</h2>
      {form.error && <ErrorMessage>{form.error}</ErrorMessage>}
      <form onSubmit={form.handleSubmit} className="space-y-4">
        <TextField
          label="Name"
          required
          value={form.name}
          onChange={form.setName}
          placeholder="Buerogebaeude Nord"
        />
        <TextField
          label="Projektnummer (optional)"
          value={form.projectCode}
          onChange={form.setProjectCode}
          placeholder="2024-042"
        />
        <ThresholdField value={form.threshold} onChange={form.setThreshold} />
        <TradeField selected={form.trades} onToggle={form.toggleTrade} />
        <SubmitButton saving={form.saving} disabled={form.saving || !form.name} />
      </form>
    </section>
  )
}

/** Buendelt Formularwerte und das Anlegen des Projekts. */
function useProjectForm() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [projectCode, setProjectCode] = useState('')
  const [threshold, setThreshold] = useState(85)
  const [trades, setTrades] = useState<Gewerk[]>(['HLK'])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  function toggleTrade(trade: Gewerk) {
    setTrades((current) =>
      current.includes(trade)
        ? current.filter((entry) => entry !== trade)
        : [...current, trade],
    )
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      // gewerk_scope bleibt der Feldname des Backends
      const project = await createProject({
        name,
        project_code: projectCode || null,
        gewerk_scope: trades,
        fuzzy_threshold: threshold,
      })
      navigate(`/projects/${project.id}/uploads`)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause))
    } finally {
      setSaving(false)
    }
  }

  return {
    name,
    setName,
    projectCode,
    setProjectCode,
    threshold,
    setThreshold,
    trades,
    toggleTrade,
    error,
    saving,
    handleSubmit,
  }
}

interface TextFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  required?: boolean
}

function TextField({ label, value, onChange, placeholder, required }: TextFieldProps) {
  return (
    <label className="block space-y-1">
      <span className={labelClass}>{label}</span>
      <input
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={inputClass}
        placeholder={placeholder}
      />
    </label>
  )
}

interface ThresholdFieldProps {
  value: number
  onChange: (value: number) => void
}

function ThresholdField({ value, onChange }: ThresholdFieldProps) {
  return (
    <label className="block space-y-1">
      <span className={labelClass}>Fuzzy-Threshold: {value}</span>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
      />
    </label>
  )
}

interface TradeFieldProps {
  selected: Gewerk[]
  onToggle: (trade: Gewerk) => void
}

function TradeField({ selected, onToggle }: TradeFieldProps) {
  return (
    <fieldset className="space-y-2">
      <legend className={labelClass}>Gewerke</legend>
      <div className="flex gap-4">
        {TRADES.map((trade) => (
          <label key={trade} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={selected.includes(trade)}
              onChange={() => onToggle(trade)}
            />
            {trade}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

function SubmitButton({ saving, disabled }: { saving: boolean; disabled: boolean }) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
    >
      {saving ? 'Wird angelegt…' : 'Projekt anlegen'}
    </button>
  )
}
