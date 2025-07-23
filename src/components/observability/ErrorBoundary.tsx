/**
 * Error Boundary for Observability Components
 * Provides error handling and recovery for agent observability components
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { Component } from 'react'
import { Alert, AlertDescription } from '../ui/alert';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { AlertTriangle, RefreshCw, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retryCount: number;
}

export class ObservabilityErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo
    });

    // Log error to console for debugging
    console.error('Observability Error Boundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-red-800">
              <AlertTriangle className="h-5 w-5" />
              <span>Something went wrong</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert className="border-red-200 bg-red-50">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                An error occurred while loading the agent observability dashboard.
                {this.state.retryCount > 0 && (
                  <span className="block mt-1 text-sm">
                    Retry attempt: {this.state.retryCount}
                  </span>
                )}
              </AlertDescription>
            </Alert>

            {this.props.showDetails && this.state.error && (
              <Card className="border-gray-200">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2 text-sm">
                    <Bug className="h-4 w-4" />
                    <span>Error Details</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div>
                      <p className="text-xs font-medium text-gray-600">Error Message:</p>
                      <p className="text-sm text-gray-800 font-mono bg-gray-100 p-2 rounded">
                        {this.state.error.message}
                      </p>
                    </div>
                    {this.state.error.stack && (
                      <div>
                        <p className="text-xs font-medium text-gray-600">Stack Trace:</p>
                        <pre className="text-xs text-gray-800 font-mono bg-gray-100 p-2 rounded overflow-auto max-h-32">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            <div className="flex space-x-3">
              <Button
                onClick={this.handleRetry}
                className="flex items-center space-x-2"
                disabled={this.state.retryCount >= 3}
              >
                <RefreshCw className="h-4 w-4" />
                <span>
                  {this.state.retryCount >= 3 ? 'Max retries reached' : 'Try Again'}
                </span>
              </Button>
              
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
                className="flex items-center space-x-2"
              >
                <RefreshCw className="h-4 w-4" />
                <span>Reload Page</span>
              </Button>
            </div>

            <div className="text-xs text-gray-500">
              If this problem persists, please contact your system administrator.
            </div>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}

// Loading Error Component
export const LoadingError: React.FC<{
  error: string;
  onRetry?: () => void;
  canRetry?: boolean;
}> = ({ error, onRetry, canRetry = true }) => {
  return (
    <Card className="border-yellow-200 bg-yellow-50">
      <CardContent className="flex flex-col items-center justify-center py-8">
        <AlertTriangle className="h-8 w-8 text-yellow-600 mb-4" />
        <h3 className="text-lg font-medium text-yellow-900 mb-2">Loading Failed</h3>
        <p className="text-yellow-800 text-center mb-4">{error}</p>
        {canRetry && onRetry && (
          <Button
            onClick={onRetry}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Retry</span>
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

// Network Error Component
export const NetworkError: React.FC<{
  onRetry?: () => void;
}> = ({ onRetry }) => {
  return (
    <Card className="border-red-200 bg-red-50">
      <CardContent className="flex flex-col items-center justify-center py-8">
        <AlertTriangle className="h-8 w-8 text-red-600 mb-4" />
        <h3 className="text-lg font-medium text-red-900 mb-2">Connection Error</h3>
        <p className="text-red-800 text-center mb-4">
          Unable to connect to the monitoring service. Please check your network connection.
        </p>
        {onRetry && (
          <Button
            onClick={onRetry}
            variant="outline"
            className="flex items-center space-x-2"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Retry Connection</span>
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default ObservabilityErrorBoundary;