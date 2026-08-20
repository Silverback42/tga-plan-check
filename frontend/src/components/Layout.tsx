import { Outlet } from 'react-router-dom'

import { Sidebar } from './Sidebar'

export function Layout() {
  return (
    <div className="flex h-full bg-slate-100">
      <Sidebar />
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
