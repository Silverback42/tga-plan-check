import { NavLink, Outlet, useParams } from 'react-router-dom'

interface NavItem {
  to: string
  label: string
}

/** Navigation innerhalb eines Projekts — erst aktiv, wenn ein Projekt gewaehlt ist. */
function projectNav(projectId: string): NavItem[] {
  return [
    { to: `/projects/${projectId}/uploads`, label: 'Uploads' },
    { to: `/projects/${projectId}/anlagen`, label: 'Anlagen' },
    { to: `/projects/${projectId}/diff`, label: 'Abgleich' },
    { to: `/projects/${projectId}/report`, label: 'Report' },
  ]
}

const linkClass = ({ isActive }: { isActive: boolean }) =>
  [
    'block rounded-md px-3 py-2 text-sm transition-colors',
    isActive
      ? 'bg-blue-600 text-white'
      : 'text-slate-300 hover:bg-slate-700 hover:text-white',
  ].join(' ')

export function Layout() {
  const { projectId } = useParams<{ projectId: string }>()

  return (
    <div className="flex h-full bg-slate-100">
      <aside className="flex w-60 shrink-0 flex-col bg-slate-800 p-4">
        <NavLink to="/" className="mb-6 block text-lg font-semibold text-white">
          TGA Plan Check
        </NavLink>

        <nav className="space-y-1">
          <NavLink to="/" end className={linkClass}>
            Projekte
          </NavLink>

          {projectId && (
            <>
              <p className="px-3 pt-4 pb-1 text-xs uppercase tracking-wide text-slate-500">
                Projekt {projectId}
              </p>
              {projectNav(projectId).map((item) => (
                <NavLink key={item.to} to={item.to} className={linkClass}>
                  {item.label}
                </NavLink>
              ))}
            </>
          )}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-slate-200 bg-white px-8 py-4">
          <h1 className="text-base font-medium text-slate-700">
            Grundriss-Schema-Abgleich
          </h1>
        </header>
        <main className="flex-1 overflow-auto p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
