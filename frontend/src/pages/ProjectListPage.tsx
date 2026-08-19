import { Link } from 'react-router-dom'

import { listProjects } from '../api/client'
import { EmptyState, ErrorMessage, Loading } from '../components/Feedback'
import { useAsync } from '../hooks/useAsync'

export function ProjectListPage() {
  const { data: projects, loading, error } = useAsync(() => listProjects(), [])

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-800">Projekte</h2>
        <Link
          to="/projects/new"
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Neues Projekt
        </Link>
      </div>

      {loading && <Loading>Projekte werden geladen…</Loading>}
      {error && <ErrorMessage>{error}</ErrorMessage>}
      {projects && projects.length === 0 && (
        <EmptyState>Noch keine Projekte angelegt.</EmptyState>
      )}

      {projects && projects.length > 0 && (
        <ul className="divide-y divide-slate-200 rounded-md border border-slate-200 bg-white">
          {projects.map((project) => (
            <li key={project.id}>
              <Link
                to={`/projects/${project.id}/uploads`}
                className="flex items-center justify-between px-4 py-3 hover:bg-slate-50"
              >
                <span className="font-medium text-slate-800">{project.name}</span>
                <span className="text-sm text-slate-500">
                  {project.project_code ?? `#${project.id}`} · Threshold{' '}
                  {project.fuzzy_threshold}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
