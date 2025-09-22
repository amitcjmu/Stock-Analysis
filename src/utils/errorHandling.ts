/**
 * Centralized error handling utilities
 * Provides consistent error messages and handling patterns across the application
 */

export interface ApiError {
  status?: number;
  code?: string;
  message?: string;
  isAuthError?: boolean;
  isForbidden?: boolean;
  isTimeout?: boolean;
  isRateLimited?: boolean;
  requestId?: string;
  name?: string;
  retryAfter?: number;
}

// Extended error type that includes common error properties
export type ErrorLike = ApiError | Error | { message?: string; status?: number; [key: string]: unknown } | unknown;

/**
 * Get a user-friendly error message based on the error type
 */
export function getUserFriendlyErrorMessage(error: ErrorLike): string {
  // Handle network errors
  if (!navigator.onLine) {
    return 'No internet connection. Please check your network and try again.';
  }

  // Handle API errors
  if (error?.status) {
    switch (error.status) {
      case 400:
        return error.message || 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Authentication required. Please log in and try again.';
      case 403:
        return 'Access denied. You may not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found. The service may not be configured yet.';
      case 409:
        return 'Conflict detected. The operation cannot be completed due to a conflict with the current state.';
      case 429:
        return 'Too many requests. Please wait a moment and try again.';
      case 500:
        return 'Server error occurred. Please try again later.';
      case 503:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        if (error.status >= 500) {
          return 'Server error occurred. Please try again later.';
        } else if (error.status >= 400) {
          return error.message || 'Request failed. Please check your input and try again.';
        }
    }
  }

  // Handle timeout errors
  if (error?.isTimeout || error?.name === 'AbortError') {
    return 'Request timed out. The service may be processing a large dataset. Please try again.';
  }

  // Handle rate limiting
  if (error?.isRateLimited) {
    return 'Rate limit exceeded. Please wait a moment and try again.';
  }

  // Fallback to error message or generic message
  return error?.message || 'An unexpected error occurred. Please try again.';
}

/**
 * Get error title based on the error type
 */
export function getErrorTitle(error: ErrorLike): string {
  if (!navigator.onLine) {
    return 'Network Error';
  }

  if (error?.status) {
    switch (error.status) {
      case 400:
        return 'Invalid Request';
      case 401:
        return 'Authentication Required';
      case 403:
        return 'Access Denied';
      case 404:
        return 'Not Found';
      case 409:
        return 'Conflict';
      case 429:
        return 'Too Many Requests';
      case 500:
      case 502:
      case 503:
        return 'Server Error';
      default:
        if (error.status >= 500) {
          return 'Server Error';
        } else if (error.status >= 400) {
          return 'Request Error';
        }
    }
  }

  if (error?.isTimeout || error?.name === 'AbortError') {
    return 'Request Timeout';
  }

  if (error?.isRateLimited) {
    return 'Rate Limited';
  }

  return 'Error';
}

/**
 * Determine if an error is retryable
 */
export function isRetryableError(error: ErrorLike): boolean {
  // Don't retry authentication or permission errors
  if (error?.status === 401 || error?.status === 403) {
    return false;
  }

  // Don't retry client errors (400-499), except for 404, 409, 429
  if (error?.status >= 400 && error?.status < 500) {
    return error.status === 404 || error.status === 409 || error.status === 429;
  }

  // Retry server errors, timeout errors, network errors
  if (error?.status >= 500 || error?.isTimeout || error?.name === 'AbortError') {
    return true;
  }

  // Retry rate limit errors after delay
  if (error?.isRateLimited) {
    return true;
  }

  // Retry network errors
  if (!navigator.onLine) {
    return true;
  }

  // Default to retryable for unknown errors
  return true;
}

/**
 * Get suggested retry delay in milliseconds
 */
export function getRetryDelay(error: ErrorLike): number {
  if (error?.retryAfter) {
    return error.retryAfter;
  }

  if (error?.isRateLimited) {
    return 2000; // 2 seconds for rate limiting
  }

  if (error?.status === 429) {
    return 2000; // 2 seconds for too many requests
  }

  if (error?.status >= 500) {
    return 1000; // 1 second for server errors
  }

  return 500; // 500ms default
}

/**
 * Format error for logging while keeping user data private
 */
export function formatErrorForLogging(error: ErrorLike, context?: string): string {
  const parts = [];

  if (context) {
    parts.push(`[${context}]`);
  }

  if (error?.status) {
    parts.push(`HTTP ${error.status}`);
  }

  if (error?.code) {
    parts.push(`Code: ${error.code}`);
  }

  if (error?.requestId) {
    parts.push(`Request: ${error.requestId}`);
  }

  if (error?.message) {
    parts.push(`Message: ${error.message}`);
  }

  return parts.length > 0 ? parts.join(' - ') : 'Unknown error';
}

/**
 * Toast notification options for different error types
 */
export function getErrorToastOptions(error: ErrorLike): {
  title: string;
  description: string;
  variant: "destructive";
  duration: number;
} {
  return {
    title: getErrorTitle(error),
    description: getUserFriendlyErrorMessage(error),
    variant: "destructive" as const,
    duration: error?.status === 404 ? 10000 : 5000, // Show 404 errors longer
  };
}
