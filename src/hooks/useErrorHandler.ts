/**
 * Error Handler Hook - CC hook for async error handling
 */

import type { ErrorInfo } from 'react';
import { toast } from 'sonner';

export const useErrorHandler = (): any => {
  const handleError = (error: Error | ErrorInfo, context?: string): void => {
    const errorInfo: ErrorInfo = error instanceof Error ? {
      message: error.message,
      timestamp: new Date(),
      component: context,
      retryable: true
    } : error;

    console.error('Async error:', errorInfo);

    // Show user-friendly error message
    toast.error(
      `An error occurred${context ? ` in ${context}` : ''}`,
      {
        description: error instanceof Error ? error.message : 'Unknown error',
        duration: 5000,
        action: {
          label: 'Retry',
          onClick: () => window.location.reload()
        }
      }
    );
  };

  return { handleError };
};
