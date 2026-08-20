/** Wiederverwendbare Zustands-Anzeigen fuer Laden, Fehler und leere Listen. */

interface MessageProps {
  children: React.ReactNode
}

export function Loading({ children }: MessageProps) {
  return <p className="text-sm text-slate-500">{children}</p>
}

export function ErrorMessage({ children }: MessageProps) {
  // role="alert": Fehler erscheinen asynchron und muessen vorgelesen werden
  return (
    <div
      role="alert"
      className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
    >
      {children}
    </div>
  )
}

export function EmptyState({ children }: MessageProps) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">
      {children}
    </div>
  )
}

/** Angezeigt, wenn die Route keine gueltige Projekt-ID enthaelt. */
export function InvalidProjectId() {
  return (
    <ErrorMessage>
      Ungueltige Projekt-ID in der Adresse — bitte ein Projekt aus der Liste
      waehlen.
    </ErrorMessage>
  )
}
