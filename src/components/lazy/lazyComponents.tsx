/**
 * Lazy Loading Internal Components
 *
 * Internal components used by lazy factories.
 * Separated from factory functions to maintain react-refresh compatibility.
 */

import React from 'react';
import { useBundlePerformance } from '../../utils/performance/hooks';

// Enhanced loading fallback with performance tracking
export const LoadingFallbackWithPerformance: React.FC<{
  message?: string;
  bundleName?: string;
}> = ({ message = 'Loading...', bundleName }) => {
  const { loadingStats } = useBundlePerformance();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">{message}</p>
        {process.env.NODE_ENV === 'development' && bundleName && (
          <div className="text-xs text-gray-400 mt-2">
            Bundle: {bundleName} | Loaded: {loadingStats.loadedBundles}/{loadingStats.totalBundles}
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced error fallback
export const ErrorFallback: React.FC<{
  error: Error;
  resetErrorBoundary: () => void;
  bundleName?: string;
}> = ({ error, resetErrorBoundary, bundleName }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center max-w-md">
      <div className="text-red-500 text-6xl mb-4">⚠️</div>
      <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
      <p className="text-gray-600 mb-4">
        Failed to load the requested component.
      </p>
      {process.env.NODE_ENV === 'development' && (
        <details className="text-left bg-gray-100 p-3 rounded mb-4 text-sm">
          <summary className="cursor-pointer font-medium">Error Details</summary>
          <pre className="mt-2 text-xs overflow-auto">
            Bundle: {bundleName || 'Unknown'}
            {'\n'}
            {error.message}
            {'\n'}
            {error.stack}
          </pre>
        </details>
      )}
      <button
        onClick={resetErrorBoundary}
        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
      >
        Try Again
      </button>
    </div>
  </div>
);
