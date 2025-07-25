/**
 * AdminLoadingState Component
 * Consistent loading state for admin components
 */

import React from 'react';

export interface AdminLoadingStateProps {
  message?: string;
  fullScreen?: boolean;
  className?: string;
}

export const AdminLoadingState: React.FC<AdminLoadingStateProps> = ({
  message = "Loading Dashboard...",
  fullScreen = false,
  className = ''
}) => {
  const containerClasses = fullScreen
    ? "flex items-center justify-center min-h-screen"
    : "container mx-auto p-6";

  return (
    <div className={`${containerClasses} ${className}`}>
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="ml-4 text-muted-foreground">{message}</p>
      </div>
    </div>
  );
};

export interface AdminErrorStateProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const AdminErrorState: React.FC<AdminErrorStateProps> = ({
  message = "Failed to load dashboard data. Please try again later.",
  onRetry,
  className = ''
}) => {
  return (
    <div className={`container mx-auto p-6 ${className}`}>
      <div className="text-center">
        <p className="text-red-500 mb-4">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-blue-600 hover:text-blue-800 underline"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
};
