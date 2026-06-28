import { AlertTriangle } from 'lucide-react'
import { Component, type ErrorInfo, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  override state: State = {
    hasError: false,
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    void error
    void errorInfo
    // Hook for external monitoring integration.
  }

  override render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
          <AlertTriangle className="h-10 w-10 text-danger" />
          <h1 className="text-2xl font-semibold text-foreground">Something went wrong.</h1>
          <p className="max-w-md text-sm text-muted-foreground">
            FXPilot hit an unexpected error. Reload to continue safely.
          </p>
          <Button onClick={() => window.location.reload()}>Reload dashboard</Button>
        </div>
      )
    }

    return this.props.children
  }
}
