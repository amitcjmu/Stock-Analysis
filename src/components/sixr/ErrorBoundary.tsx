import type { ReactNode, ErrorInfo } from 'react';
import React from 'react'
import { Component } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Separator } from '../ui/separator';
import {
  AlertTriangle,
  RefreshCw,
  Bug,
  Wifi,
  Server,
  Clock,
  ChevronDown,
  ChevronUp,
  Copy,
  ExternalLink,
  Home
} from 'lucide-react';
import { toast } from 'sonner';

// Error types
export interface ErrorInfo {
  message: string;
  code?: string;
  status?: number;
  details?: Record<string, unknown>;
  timestamp: Date;
  component?: string;
  action?: string;
  retryable?: boolean;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: ErrorInfo | null;
  errorId: string | null;
  showDetails: boolean;
  retryCount: number;
  isRetrying: boolean;
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: ErrorInfo, errorId: string) => void;
  onRetry?: () => void;
  maxRetries?: number;
  showErrorDetails?: boolean;
  enableReporting?: boolean;
  component?: string;
}

// Error classification
const getErrorType = (error: ErrorInfo): 'network' | 'server' | 'client' | 'unknown' => {
  if (error.code === 'NETWORK_ERROR' || error.status === 0) {
    return 'network';
  }
  if (error.status && error.status >= 500) {
    return 'server';
  }
  if (error.status && error.status >= 400 && error.status < 500) {
    return 'client';
  }
  return 'unknown';
};

const getErrorIcon = (type: string): JSX.Element => {
  switch (type) {
    case 'network': return <Wifi className="h-5 w-5" />;
    case 'server': return <Server className="h-5 w-5" />;
    case 'client': return <AlertTriangle className="h-5 w-5" />;
    default: return <Bug className="h-5 w-5" />;
  }
};

const getErrorColor = (type: string): unknown => {
  switch (type) {
    case 'network': return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'server': return 'text-red-600 bg-red-50 border-red-200';
    case 'client': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

const getErrorMessage = (error: ErrorInfo): { title: string; description: string; suggestion: string } => {
  const type = getErrorType(error);

  switch (type) {
    case 'network':
      return {
        title: 'Connection Problem',
        description: 'Unable to connect to the server. Please check your internet connection.',
        suggestion: 'Try refreshing the page or check your network connection.'
      };
    case 'server':
      return {
        title: 'Server Error',
        description: 'The server encountered an error while processing your request.',
        suggestion: 'Please try again in a few moments. If the problem persists, contact support.'
      };
    case 'client':
      return {
        title: 'Request Error',
        description: error.message || 'There was a problem with your request.',
        suggestion: 'Please check your input and try again.'
      };
    default:
      return {
        title: 'Unexpected Error',
        description: error.message || 'An unexpected error occurred.',
        suggestion: 'Please try refreshing the page. If the problem persists, contact support.'
      };
  }
};

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private retryTimeoutId: NodeJS.Timeout | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorId: null,
      showDetails: false,
      retryCount: 0,
      isRetrying: false
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    const errorInfo: ErrorInfo = {
      message: error.message,
      timestamp: new Date(),
      retryable: true
    };

    const errorId = `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    return {
      hasError: true,
      error: errorInfo,
      errorId,
      showDetails: false,
      isRetrying: false
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const enhancedError: ErrorInfo = {
      message: error.message,
      details: {
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        errorBoundary: this.props.component || 'Unknown'
      },
      timestamp: new Date(),
      component: this.props.component,
      retryable: true
    };

    console.error('ErrorBoundary caught an error:', error, errorInfo);

    if (this.props.onError && this.state.errorId) {
      this.props.onError(enhancedError, this.state.errorId);
    }

    // Report error if enabled
    if (this.props.enableReporting) {
      this.reportError(enhancedError);
    }
  }

  componentWillUnmount(): unknown {
    if (this.retryTimeoutId) {
      clearTimeout(this.retryTimeoutId);
    }
  }

  private reportError = async (error: ErrorInfo) => {
    try {
      // In a real application, this would send to an error reporting service
      console.log('Reporting error:', error);

      // Example: Send to error reporting service
      // await fetch('/api/errors', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     error,
      //     errorId: this.state.errorId,
      //     userAgent: navigator.userAgent,
      //     url: window.location.href,
      //     timestamp: new Date().toISOString()
      //   })
      // });
    } catch (reportingError) {
      console.error('Failed to report error:', reportingError);
    }
  };

  private handleRetry = () => {
    const { maxRetries = 3 } = this.props;

    if (this.state.retryCount >= maxRetries) {
      toast.error('Maximum retry attempts reached');
      return;
    }

    this.setState({ isRetrying: true });

    // Simulate retry delay
    this.retryTimeoutId = setTimeout(() => {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorId: null,
        showDetails: false,
        retryCount: prevState.retryCount + 1,
        isRetrying: false
      }));

      if (this.props.onRetry) {
        this.props.onRetry();
      }

      toast.success('Retrying...');
    }, 1000);
  };

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorId: null,
      showDetails: false,
      retryCount: 0,
      isRetrying: false
    });
  };

  private handleCopyError = () => {
    if (this.state.error) {
      const errorText = JSON.stringify({
        message: this.state.error.message,
        code: this.state.error.code,
        status: this.state.error.status,
        timestamp: this.state.error.timestamp,
        errorId: this.state.errorId,
        details: this.state.error.details
      }, null, 2);

      navigator.clipboard.writeText(errorText).then(() => {
        toast.success('Error details copied to clipboard');
      }).catch(() => {
        toast.error('Failed to copy error details');
      });
    }
  };

  private toggleDetails = () => {
    this.setState(prevState => ({
      showDetails: !prevState.showDetails
    }));
  };

  render(): unknown {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const errorType = getErrorType(this.state.error);
      const { title, description, suggestion } = getErrorMessage(this.state.error);
      const { maxRetries = 3 } = this.props;
      const canRetry = this.state.error.retryable && this.state.retryCount < maxRetries;

      return (
        <div className="min-h-[400px] flex items-center justify-center p-4">
          <Card className={`w-full max-w-2xl ${getErrorColor(errorType)}`}>
            <CardHeader>
              <div className="flex items-center space-x-3">
                {getErrorIcon(errorType)}
                <div className="flex-1">
                  <CardTitle className="text-lg">{title}</CardTitle>
                  <CardDescription className="mt-1">
                    {description}
                  </CardDescription>
                </div>
                <Badge variant="outline" className="ml-auto">
                  {errorType}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Error suggestion */}
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>What can you do?</AlertTitle>
                <AlertDescription>{suggestion}</AlertDescription>
              </Alert>

              {/* Error metadata */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Error ID:</span>
                  <span className="ml-2 font-mono text-xs">{this.state.errorId}</span>
                </div>
                <div>
                  <span className="font-medium">Time:</span>
                  <span className="ml-2">{this.state.error.timestamp.toLocaleString()}</span>
                </div>
                {this.state.error.code && (
                  <div>
                    <span className="font-medium">Code:</span>
                    <span className="ml-2 font-mono">{this.state.error.code}</span>
                  </div>
                )}
                {this.state.error.status && (
                  <div>
                    <span className="font-medium">Status:</span>
                    <span className="ml-2">{this.state.error.status}</span>
                  </div>
                )}
              </div>

              {/* Retry information */}
              {this.state.retryCount > 0 && (
                <div className="text-sm text-gray-600">
                  <Clock className="h-4 w-4 inline mr-1" />
                  Retry attempt {this.state.retryCount} of {maxRetries}
                </div>
              )}

              <Separator />

              {/* Action buttons */}
              <div className="flex flex-wrap gap-2">
                {canRetry && (
                  <Button
                    onClick={this.handleRetry}
                    disabled={this.state.isRetrying}
                    className="flex items-center space-x-2"
                  >
                    <RefreshCw className={`h-4 w-4 ${this.state.isRetrying ? 'animate-spin' : ''}`} />
                    <span>{this.state.isRetrying ? 'Retrying...' : 'Try Again'}</span>
                  </Button>
                )}

                <Button variant="outline" onClick={this.handleReset}>
                  <Home className="h-4 w-4 mr-2" />
                  Reset
                </Button>

                <Button variant="outline" onClick={this.handleCopyError}>
                  <Copy className="h-4 w-4 mr-2" />
                  Copy Error
                </Button>

                {this.props.showErrorDetails && (
                  <Button variant="outline" onClick={this.toggleDetails}>
                    {this.state.showDetails ? (
                      <>
                        <ChevronUp className="h-4 w-4 mr-2" />
                        Hide Details
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-4 w-4 mr-2" />
                        Show Details
                      </>
                    )}
                  </Button>
                )}

                <Button variant="outline" asChild>
                  <a href="/support" target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Get Help
                  </a>
                </Button>
              </div>

              {/* Error details */}
              {this.state.showDetails && this.state.error.details && (
                <div className="mt-4">
                  <Separator />
                  <div className="mt-4">
                    <h4 className="font-medium mb-2">Technical Details</h4>
                    <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-40">
                      {JSON.stringify(this.state.error.details, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}


export default ErrorBoundary;
