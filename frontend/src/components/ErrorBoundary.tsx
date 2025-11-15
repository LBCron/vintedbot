import { Component, ReactNode } from 'react';
import { GlassCard } from './ui/GlassCard';
import { Button } from './ui/Button';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: any | null;
}

/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the component tree,
 * logs those errors, and displays a fallback UI
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null
    };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    // Log error to console
    console.error('Error caught by boundary:', error, errorInfo);

    // Send to error tracking service (Sentry)
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack
          }
        }
      });
    }

    // Update state with error info
    this.setState({
      error,
      errorInfo
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
          <GlassCard className="p-8 max-w-2xl w-full">
            {/* Icon */}
            <div className="text-center mb-6">
              <div className="w-20 h-20 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-10 h-10 text-red-400" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">
                Oops! Something went wrong
              </h2>
              <p className="text-slate-400">
                An unexpected error occurred. Don't worry, your data is safe.
              </p>
            </div>

            {/* Error Details (Development only) */}
            {import.meta.env.DEV && this.state.error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                <div className="text-red-400 font-mono text-sm mb-2">
                  {this.state.error.toString()}
                </div>
                {this.state.errorInfo && (
                  <details className="mt-2">
                    <summary className="text-slate-400 text-xs cursor-pointer hover:text-white">
                      Component Stack
                    </summary>
                    <pre className="mt-2 text-xs text-slate-500 overflow-auto max-h-40">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={this.handleReset}
                variant="outline"
                icon={RefreshCw}
              >
                Try Again
              </Button>
              <Button
                onClick={this.handleReload}
                variant="outline"
                icon={RefreshCw}
              >
                Reload Page
              </Button>
              <Button
                onClick={this.handleGoHome}
                icon={Home}
              >
                Go to Dashboard
              </Button>
            </div>

            {/* Help Text */}
            <div className="mt-6 text-center">
              <p className="text-sm text-slate-500">
                If this problem persists, please{' '}
                <a
                  href="https://github.com/LBCron/vintedbot/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-violet-400 hover:text-violet-300 underline"
                >
                  report the issue
                </a>
                .
              </p>
            </div>
          </GlassCard>
        </div>
      );
    }

    return this.props.children;
  }
}
