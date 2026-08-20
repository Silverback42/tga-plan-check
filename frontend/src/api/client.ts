/** Typisierter API-Client fuer das FastAPI-Backend. */

import type {
  Anlage,
  DiffEntry,
  DiffSummary,
  DiffType,
  Gewerk,
  MatchReviewItem,
  PlanType,
  Project,
  ProjectCreate,
  Task,
  Upload,
} from './types'

// Im Dev-Betrieb proxied Vite /api an das Backend (siehe vite.config.ts)
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

/** Fehler mit HTTP-Status, damit die UI gezielt reagieren kann. */
export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** Liest die Fehlermeldung aus dem FastAPI-Detail-Feld, falls vorhanden. */
async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') {
      return body.detail
    }
    return JSON.stringify(body?.detail ?? body)
  } catch {
    // Kein JSON-Body — Statustext ist die beste verfuegbare Information
    return response.statusText || 'Unbekannter Fehler'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, init)
  } catch (cause) {
    // Netzwerkfehler: Ursache anhaengen, damit sie nicht verloren geht
    const error = new ApiError(
      `Backend nicht erreichbar (${path}). Laeuft der Server auf Port 8000?`,
      0,
    )
    error.cause = cause
    throw error
  }

  return parseResponse<T>(response)
}

/** Wandelt eine erfolgreiche Antwort in Nutzdaten — 204 liefert bewusst nichts. */
async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new ApiError(await extractErrorMessage(response), response.status)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

function jsonRequest<T>(path: string, method: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

// Projects -----------------------------------------------------------------

export const listProjects = () => request<Project[]>('/projects')

export const getProject = (id: number) => request<Project>(`/projects/${id}`)

export const createProject = (data: ProjectCreate) =>
  jsonRequest<Project>('/projects', 'POST', data)

export const deleteProject = (id: number) =>
  request<void>(`/projects/${id}`, { method: 'DELETE' })

// Uploads ------------------------------------------------------------------

export const listUploads = (projectId: number) =>
  request<Upload[]>(`/projects/${projectId}/uploads`)

export function uploadPlan(
  projectId: number,
  file: File,
  planType: PlanType,
  gewerk: Gewerk,
): Promise<Upload> {
  const form = new FormData()
  form.append('file', file)
  form.append('plan_type', planType)
  form.append('gewerk', gewerk)
  // Content-Type bewusst nicht setzen: der Browser ergaenzt die Multipart-Boundary
  return request<Upload>(`/projects/${projectId}/uploads`, {
    method: 'POST',
    body: form,
  })
}

// Extraction ---------------------------------------------------------------

export const startExtraction = (projectId: number) =>
  request<Task>(`/projects/${projectId}/extract`, { method: 'POST' })

export function listAnlagen(
  projectId: number,
  planType?: PlanType,
): Promise<Anlage[]> {
  const query = planType ? `?plan_type=${planType}` : ''
  return request<Anlage[]>(`/projects/${projectId}/anlagen${query}`)
}

// Matching -----------------------------------------------------------------

export const startMatching = (projectId: number) =>
  request<Task>(`/projects/${projectId}/match`, { method: 'POST' })

export const listMatches = (projectId: number) =>
  request<MatchReviewItem[]>(`/projects/${projectId}/matches`)

// Diff ---------------------------------------------------------------------

export const startDiff = (projectId: number) =>
  request<Task>(`/projects/${projectId}/diff`, { method: 'POST' })

export function listDiff(
  projectId: number,
  diffType?: DiffType,
): Promise<DiffEntry[]> {
  const query = diffType ? `?diff_type=${diffType}` : ''
  return request<DiffEntry[]>(`/projects/${projectId}/diff${query}`)
}

export const getDiffSummary = (projectId: number) =>
  request<DiffSummary>(`/projects/${projectId}/diff/summary`)

// Reports ------------------------------------------------------------------

export const createReport = (projectId: number) =>
  request<Task>(`/projects/${projectId}/report`, { method: 'POST' })

/** Absolute URL des Downloads — wird direkt als Link-Ziel verwendet. */
export const reportDownloadUrl = (projectId: number) =>
  `${BASE_URL}/projects/${projectId}/report/download`
