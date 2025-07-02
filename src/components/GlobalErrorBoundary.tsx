import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

type GlobalErrorBoundaryProps = {
  children: React.ReactNode;
};

type State = {
  hasError: boolean;
  error: Error | null;
};

class GlobalErrorBoundary extends React.Component<GlobalErrorBoundaryProps, State> {
  state: State = {
    hasError: false,
    error: null,
  };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Global Error Boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center h-screen bg-background p-4">
          <Alert variant="destructive" className="max-w-2xl">
            <AlertTitle>Application Error</AlertTitle>
            <AlertDescription>
              <p className="mb-4">
                Something went wrong. The application has encountered an unrecoverable error.
              </p>
              <pre className="text-sm overflow-auto max-h-60 bg-gray-100 p-2 rounded mt-2">
                {this.state.error?.message || this.state.error?.toString() || 'Unknown error'}
              </pre>
              <Button 
                className="mt-4"
                onClick={this.handleReset}
              >
                Try Again
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}

export { GlobalErrorBoundary };
export default GlobalErrorBoundary;
