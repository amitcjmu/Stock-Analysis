/**
 * Loading Fallback Components - Reusable loading states
 */

import React from 'react';
import { Loader2, AlertCircle, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { LoadingPriority } from '@/types/lazy';

interface LoadingFallbackProps {
  message?: string;
  priority?: LoadingPriority;
  showProgress?: boolean;
  progress?: number;
  compact?: boolean;
}

export const LoadingFallback: React.FC<LoadingFallbackProps> = ({
  message = 'Loading...',
  priority = LoadingPriority.NORMAL,
  showProgress = false,
  progress = 0,
  compact = false
}) => {
  const getPriorityColor = (priority: LoadingPriority) => {
    switch (priority) {
      case LoadingPriority.CRITICAL:
        return 'text-red-600 border-red-200';
      case LoadingPriority.HIGH:
        return 'text-blue-600 border-blue-200';
      case LoadingPriority.NORMAL:
        return 'text-gray-600 border-gray-200';
      case LoadingPriority.LOW:
        return 'text-gray-400 border-gray-100';
      default:
        return 'text-gray-600 border-gray-200';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center space-x-2 p-4">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span className="text-sm text-gray-600">{message}</span>
      </div>
    );
  }

  return (
    <Card className={`w-full ${getPriorityColor(priority)}`}>
      <CardContent className="flex flex-col items-center justify-center p-8 text-center">
        <Loader2 className="h-8 w-8 animate-spin mb-4" />
        <h3 className="text-lg font-semibold mb-2">{message}</h3>
        {showProgress && (
          <div className="w-full max-w-xs mb-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">{progress.toFixed(0)}% loaded</p>
          </div>
        )}
        <p className="text-sm text-gray-500">
          Please wait while we load the component...
        </p>
      </CardContent>
    </Card>
  );
};

interface ErrorFallbackProps {
  error: Error;
  retry: () => void;
  componentName?: string;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  retry,
  componentName = 'Component'
}) => {
  return (
    <Card className="w-full border-red-200">
      <CardContent className="flex flex-col items-center justify-center p-8 text-center">
        <AlertCircle className="h-8 w-8 text-red-600 mb-4" />
        <h3 className="text-lg font-semibold text-red-800 mb-2">
          Failed to load {componentName}
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          {error.message || 'An unexpected error occurred while loading the component.'}
        </p>
        <Button onClick={retry} variant="outline" className="flex items-center space-x-2">
          <RotateCcw className="h-4 w-4" />
          <span>Retry</span>
        </Button>
        {process.env.NODE_ENV === 'development' && (
          <details className="mt-4 text-left w-full">
            <summary className="text-sm text-gray-500 cursor-pointer">
              Error Details (Development)
            </summary>
            <pre className="mt-2 text-xs text-gray-700 bg-gray-100 p-2 rounded overflow-auto">
              {error.stack}
            </pre>
          </details>
        )}
      </CardContent>
    </Card>
  );
};

interface SkeletonFallbackProps {
  type?: 'page' | 'card' | 'table' | 'form';
  rows?: number;
}

export const SkeletonFallback: React.FC<SkeletonFallbackProps> = ({
  type = 'page',
  rows = 3
}) => {
  switch (type) {
    case 'page':
      return (
        <div className="space-y-6 p-6">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      );

    case 'card':
      return (
        <Card>
          <CardContent className="p-6">
            <Skeleton className="h-6 w-1/2 mb-4" />
            {Array.from({ length: rows }).map((_, i) => (
              <Skeleton key={i} className="h-4 w-full mb-2" />
            ))}
          </CardContent>
        </Card>
      );

    case 'table':
      return (
        <div className="space-y-4">
          <Skeleton className="h-6 w-1/3" />
          <div className="space-y-2">
            {Array.from({ length: rows }).map((_, i) => (
              <div key={i} className="flex space-x-4">
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-4 w-1/6" />
              </div>
            ))}
          </div>
        </div>
      );

    case 'form':
      return (
        <div className="space-y-4">
          <Skeleton className="h-6 w-1/3" />
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-1/6" />
              <Skeleton className="h-10 w-full" />
            </div>
          ))}
          <Skeleton className="h-10 w-32" />
        </div>
      );

    default:
      return <Skeleton className="h-32 w-full" />;
  }
};

// Preload indicator for showing preloading activity
export const PreloadIndicator: React.FC<{ visible: boolean }> = ({ visible }) => {
  if (!visible) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-3 py-2 rounded-lg shadow-lg flex items-center space-x-2 z-50">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span className="text-sm">Preloading...</span>
    </div>
  );
};