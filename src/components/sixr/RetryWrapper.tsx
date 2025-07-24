/**
 * Retry Wrapper Component - CC component for retry logic
 */

import React from 'react'
import type { ReactNode} from 'react';
import { useState } from 'react'
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Button } from '../ui/button';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

interface RetryWrapperProps {
  children: ReactNode;
  onRetry: () => Promise<void>;
  maxRetries?: number;
  retryDelay?: number;
  fallback?: ReactNode;
}

export const RetryWrapper: React.FC<RetryWrapperProps> = ({
  children,
  onRetry,
  maxRetries = 3,
  retryDelay = 1000,
  fallback
}) => {
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRetry = async () => {
    if (retryCount >= maxRetries) {
      toast.error('Maximum retry attempts reached');
      return;
    }

    setIsRetrying(true);
    setError(null);

    try {
      await new Promise(resolve => setTimeout(resolve, retryDelay));
      await onRetry();
      setRetryCount(0);
      toast.success('Operation completed successfully');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Retry failed';
      setError(errorMessage);
      setRetryCount(prev => prev + 1);
      toast.error(`Retry ${retryCount + 1} failed: ${errorMessage}`);
    } finally {
      setIsRetrying(false);
    }
  };

  if (error && retryCount >= maxRetries) {
    return fallback || (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Operation Failed</AlertTitle>
        <AlertDescription>
          Maximum retry attempts ({maxRetries}) reached. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  if (isRetrying) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex items-center space-x-3">
          <RefreshCw className="h-5 w-5 animate-spin" />
          <span>Retrying... (Attempt {retryCount + 1} of {maxRetries})</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="m-4">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Operation Failed</AlertTitle>
        <AlertDescription className="mt-2">
          {error}
          <Button
            variant="outline"
            size="sm"
            onClick={handleRetry}
            className="ml-2"
            disabled={retryCount >= maxRetries}
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Retry ({retryCount + 1}/{maxRetries})
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return <>{children}</>;
};