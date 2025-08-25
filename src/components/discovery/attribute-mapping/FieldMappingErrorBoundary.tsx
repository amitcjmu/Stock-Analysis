import type { ErrorInfo, ReactNode } from 'react';
import React from 'react'
import { Component } from 'react'
import { AlertTriangle, RefreshCw, WifiOff, Brain, MessageCircle } from 'lucide-react';

interface Analytics {
  track: (event: string, properties: {
    error: string;
    stack?: string;
    componentStack: string;
  }) => void;
}

declare global {
  interface Window {
    analytics?: Analytics;
  }
}

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
  errorType: 'network' | 'processing' | 'learning' | 'unknown';
  retryCount: number;
}

export class FieldMappingErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      errorType: 'unknown',
      retryCount: 0
    };
  }

  private static categorizeError(error: Error): 'network' | 'processing' | 'learning' | 'unknown' {
    const message = error.message.toLowerCase();

    if (message.includes('404') || message.includes('network') || message.includes('fetch')) {
      return 'network';
    }
    if (message.includes('learning') || message.includes('pattern') || message.includes('ai')) {
      return 'learning';
    }
    if (message.includes('mapping') || message.includes('validation') || message.includes('processing')) {
      return 'processing';
    }

    return 'unknown';
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
      errorType: FieldMappingErrorBoundary.categorizeError(error)
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ error, errorInfo });
    console.error('Field mapping error:', error, errorInfo);

    // Log to monitoring service if available
    if (typeof window !== 'undefined' && window.analytics) {
      window.analytics.track('Field Mapping Error', {
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      });
    }
  }

  handleReload = (): void => {
    window.location.reload();
  };

  handleRetry = (): void => {
    const maxRetries = 3;
    if (this.state.retryCount >= maxRetries) {
      return;
    }

    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      retryCount: this.state.retryCount + 1
    });
  };

  getErrorIcon = (): JSX.Element => {
    switch (this.state.errorType) {
      case 'network':
        return <WifiOff className="h-6 w-6 text-red-600" />;
      case 'learning':
        return <Brain className="h-6 w-6 text-orange-600" />;
      case 'processing':
        return <AlertTriangle className="h-6 w-6 text-yellow-600" />;
      default:
        return <AlertTriangle className="h-6 w-6 text-red-600" />;
    }
  };

  getErrorTitle = (): string => {
    switch (this.state.errorType) {
      case 'network':
        return 'Field Mapping Service Unavailable';
      case 'learning':
        return 'AI Learning System Error';
      case 'processing':
        return 'Field Mapping Processing Error';
      default:
        return 'Field Mapping Error';
    }
  };

  getErrorMessage = (): string => {
    if (!this.state.error) return 'An unexpected error occurred.';

    const message = this.state.error.message;

    if (message.includes('404')) {
      return 'The field mapping endpoints have been updated. Please refresh the page and try again. If the issue persists, contact support.';
    }
    if (message.includes('403') || message.includes('401')) {
      return 'Authentication expired. Please refresh the page and log in again.';
    }
    if (message.includes('500')) {
      return 'Server error occurred while processing field mappings. Please try again in a few moments.';
    }
    if (this.state.errorType === 'learning') {
      return 'The AI learning system encountered an issue. Field mappings will continue to work, but learning may be temporarily disabled.';
    }

    return message || 'Something went wrong with the field mapping functionality.';
  };

  render(): unknown {
    if (this.state.hasError) {
      const maxRetries = 3;

      return (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8 border border-red-200">
          <div className="flex items-center space-x-3 mb-4">
            {this.getErrorIcon()}
            <h2 className="text-lg font-semibold text-red-900">{this.getErrorTitle()}</h2>
          </div>

          <div className="mb-4">
            <p className="text-gray-700 mb-3">
              {this.getErrorMessage()}
            </p>

            {this.state.errorType === 'learning' && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-3">
                <div className="flex items-center gap-2 text-orange-700 mb-1">
                  <Brain className="h-4 w-4" />
                  <span className="font-medium text-sm">Learning System Status</span>
                </div>
                <p className="text-sm text-orange-600">
                  Field mappings will continue to work normally. Your manual approvals and rejections are being stored and will be processed when the system recovers.
                </p>
              </div>
            )}

            {this.state.retryCount > 0 && (
              <p className="text-sm text-gray-500 mb-2">
                Retry attempt: {this.state.retryCount} of {maxRetries}
              </p>
            )}

            {this.state.error && (
              <details className="bg-red-50 p-3 rounded text-sm">
                <summary className="cursor-pointer font-medium text-red-800 mb-2">
                  Technical Details
                </summary>
                <div className="text-red-700">
                  <div className="mb-2">
                    <strong>Error Type:</strong> {this.state.errorType}
                  </div>
                  <div className="mb-2">
                    <strong>Message:</strong> {this.state.error.message}
                  </div>
                  {this.state.error.stack && (
                    <div>
                      <strong>Stack Trace:</strong>
                      <pre className="mt-1 text-xs whitespace-pre-wrap overflow-auto max-h-32 font-mono">
                        {this.state.error.stack}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={this.handleRetry}
              disabled={this.state.retryCount >= maxRetries}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className="h-4 w-4" />
              <span>{this.state.retryCount >= maxRetries ? 'Max Retries Reached' : 'Try Again'}</span>
            </button>

            <button
              onClick={this.handleReload}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
            >
              Reload Page
            </button>

            <button
              onClick={() => {
                // Copy error info to clipboard for support
                const errorInfo = JSON.stringify({
                  type: this.state.errorType,
                  message: this.state.error?.message,
                  timestamp: new Date().toISOString(),
                  retryCount: this.state.retryCount
                }, null, 2);
                navigator.clipboard?.writeText(errorInfo);
                alert('Error details copied to clipboard');
              }}
              className="flex items-center space-x-2 px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              <MessageCircle className="h-4 w-4" />
              <span>Copy Error Info</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
