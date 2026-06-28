import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { registerSW } from 'virtual:pwa-register'

import { AppRouter } from '@/app/router'
import { AppProviders } from '@/app/providers'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import './index.css'

registerSW({ immediate: true })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AppProviders>
        <ErrorBoundary>
          <AppRouter />
        </ErrorBoundary>
      </AppProviders>
    </BrowserRouter>
  </StrictMode>,
)
