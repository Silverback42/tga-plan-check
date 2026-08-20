import { useParams } from 'react-router-dom'

/**
 * Liest die Projekt-ID aus der Route und liefert null bei ungueltigen Werten —
 * so gelangt niemals NaN in eine API-URL.
 */
export function useProjectId(): number | null {
  const { projectId } = useParams<{ projectId: string }>()
  if (!projectId || !/^\d+$/.test(projectId)) {
    return null
  }
  const id = Number(projectId)
  return Number.isSafeInteger(id) && id > 0 ? id : null
}
