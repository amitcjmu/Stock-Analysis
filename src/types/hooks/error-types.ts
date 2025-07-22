/**
 * Error handling types for hooks
 * 
 * Common error types used across hooks for consistent error handling.
 */

// API Error type
export interface ApiError extends Error {
  code?: string;
  status?: number;
  details?: Record<string, string | number | boolean>;
  timestamp?: string;
  requestId?: string;
}

// Network Error type
export interface NetworkError extends Error {
  code?: string;
  status?: number;
  response?: {
    data?: unknown;
    status?: number;
    statusText?: string;
  };
}

// Type guard for API errors
export function isApiError(error: unknown): error is ApiError {
  return error instanceof Error && 'code' in error;
}

// Type guard for network errors  
export function isNetworkError(error: unknown): error is NetworkError {
  return error instanceof Error && 'response' in error;
}

// Generic error handler type
export type ErrorHandler = (error: Error | ApiError | NetworkError | unknown) => void;

// Error with retry information
export interface RetryableError extends Error {
  retryable: boolean;
  retryAfter?: number;
  attemptNumber?: number;
  maxAttempts?: number;
}