/** TypeScript-Spiegel der Pydantic-Schemas aus dem Backend. */

export type PlanType = 'schema' | 'grundriss'
export type SourceType = 'pdf_vector' | 'pdf_scan' | 'dxf' | 'dwg'
export type Gewerk = 'HLK' | 'ELT' | 'SAN'
export type TaskType = 'extract' | 'match' | 'diff' | 'report'
export type TaskStatus = 'pending' | 'running' | 'success' | 'failed'
export type MatchStatus = 'auto' | 'confirmed' | 'rejected' | 'manual'
export type DiffType =
  | 'only_schema'
  | 'only_grundriss'
  | 'attr_mismatch'
  | 'room_mismatch'
export type Severity = 'info' | 'warning' | 'error'

export interface Project {
  id: number
  name: string
  project_code: string | null
  gewerk_scope: Gewerk[]
  fuzzy_threshold: number
  synonyms_json: Record<string, unknown>
  created_at: string
}

export interface ProjectCreate {
  name: string
  project_code?: string | null
  gewerk_scope?: Gewerk[]
  fuzzy_threshold?: number
  synonyms_json?: Record<string, unknown>
}

export interface Upload {
  id: number
  project_id: number
  filename: string
  source_type: SourceType
  plan_type: PlanType
  gewerk: Gewerk
  file_size: number | null
  uploaded_at: string
}

export interface Task {
  id: number
  project_id: number
  task_type: TaskType
  status: TaskStatus
  progress: number
  result_path: string | null
  error_message: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export interface Anlage {
  id: number
  project_id: number
  upload_id: number
  plan_type: PlanType
  gewerk: Gewerk
  label_raw: string
  label_normalized: string
  anlagentyp: string | null
  room_code: string | null
  page: number | null
  x: number | null
  y: number | null
  attributes_json: Record<string, unknown>
  aks: string | null
}

export interface MatchPair {
  id: number
  project_id: number
  schema_anlage_id: number
  grundriss_anlage_id: number
  score: number
  method: string
  status: MatchStatus
  created_at: string
}

export interface MatchReviewItem {
  match: MatchPair
  schema_anlage: Anlage
  grundriss_anlage: Anlage
}

export interface DiffEntry {
  id: number
  project_id: number
  diff_type: DiffType
  severity: Severity
  anlage_ref_id: number | null
  partner_ref_id: number | null
  details_json: Record<string, unknown>
  created_at: string
}

export interface DiffSummary {
  only_schema: number
  only_grundriss: number
  attr_mismatch: number
  room_mismatch: number
  total: number
}
