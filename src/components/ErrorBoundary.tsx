import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Thorpe UI error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-surface p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-warning" />
          <h1 className="text-xl font-bold text-white">Something went wrong</h1>
          <p className="max-w-md text-sm text-gray-400">
            Thorpe hit an unexpected error. Restart the app or return to the dashboard.
          </p>
          <button
            type="button"
            className="btn-primary text-sm"
            onClick={() => {
              this.setState({ error: null });
              window.location.hash = "#/";
              window.location.reload();
            }}
          >
            Reload Thorpe
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
