import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import App from './App.tsx'
import './index.css'

const rootElement = document.getElementById('root')
if (!rootElement) {
  // Ohne Mount-Punkt kann React nicht starten — frueh und deutlich abbrechen
  throw new Error('Mount-Element #root fehlt in index.html')
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
