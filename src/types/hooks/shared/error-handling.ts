/**
 * Error Handling Hook Types
 * 
 * Hook interfaces for error boundary management and async error handling.
 */

// Error handling hooks
export interface UseErrorBoundaryParams {
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  fallback?: React.ComponentType<{ error: Error; resetError: () => void }>;
  resetOnPropsChange?: boolean;
  resetKeys?: any[];
  onReset?: () => void;
}

export interface UseErrorBoundaryReturn {
  error: Error | null;
  resetError: () => void;
  captureError: (error: Error) => void;
}

export interface UseAsyncErrorParams {
  onError?: (error: Error) => void;
  resetOnNewAsyncOperation?: boolean;
}

export interface UseAsyncErrorReturn {
  error: Error | null;
  captureError: (error: Error) => void;
  resetError: () => void;
}