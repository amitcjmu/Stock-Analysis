/**
 * Error Interceptor for API v3
 * Handles error transformation and standardization
 */

import {
  ApiError,
  ValidationApiError,
  NotFoundApiError,
  NetworkError,
  TimeoutError,
  HttpStatusCode,
  isApiError,
  isValidationErrorResponse,
  isNotFoundErrorResponse
} from '../types/responses';

export interface ErrorConfig {
  transformErrors?: boolean;
  logErrors?: boolean;
  includeStack?: boolean;
  onError?: (error: any, request?: Request) => void;
  errorHandlers?: Record<number, (error: any, request?: Request) => any>;
}

const DEFAULT_ERROR_CONFIG: Required<ErrorConfig> = {
  transformErrors: true,
  logErrors: true,
  includeStack: process.env.NODE_ENV === 'development',
  onError: (error, request) => {
    console.error('API Error:', error);
  },
  errorHandlers: {}
};

/**
 * Create error interceptor with custom configuration
 */
export function createErrorInterceptor(config: ErrorConfig = {}) {
  const errorConfig = { ...DEFAULT_ERROR_CONFIG, ...config };

  return async (response: Response, request?: Request): Promise<Response> => {
    if (response.ok) {
      return response;
    }

    let error: any;

    try {
      // Try to parse error response
      const errorData = await response.clone().json();
      error = transformErrorResponse(errorData, response.status, request);
    } catch (parseError) {
      // If response is not JSON, create generic error
      error = new ApiError(
        response.status,
        getErrorCodeFromStatus(response.status),
        response.statusText || `HTTP ${response.status}`,
        undefined,
        request?.headers.get('X-Request-ID') || undefined
      );
    }

    // Apply custom error handlers
    if (errorConfig.errorHandlers[response.status]) {
      try {
        const handledError = errorConfig.errorHandlers[response.status](error, request);
        if (handledError) {
          error = handledError;
        }
      } catch (handlerError) {
        console.warn('Error handler failed:', handlerError);
      }
    }

    // Log error if configured
    if (errorConfig.logErrors) {
      errorConfig.onError(error, request);
    }

    throw error;
  };
}

/**
 * Transform error response to appropriate error type
 */
function transformErrorResponse(errorData: any, status: number, request?: Request): ApiError {
  const requestId = request?.headers.get('X-Request-ID') || undefined;

  // Handle validation errors
  if (isValidationErrorResponse(errorData)) {
    return ValidationApiError.fromResponse(errorData);
  }

  // Handle not found errors
  if (isNotFoundErrorResponse(errorData)) {
    return NotFoundApiError.fromResponse(errorData);
  }

  // Handle generic API errors
  if (errorData.error && errorData.message) {
    return new ApiError(
      status,
      errorData.error,
      errorData.message,
      errorData.details,
      requestId
    );
  }

  // Fallback for malformed error responses
  return new ApiError(
    status,
    getErrorCodeFromStatus(status),
    errorData.message || errorData.detail || `HTTP ${status}`,
    errorData,
    requestId
  );
}

/**
 * Get error code from HTTP status
 */
function getErrorCodeFromStatus(status: number): string {
  switch (status) {
    case HttpStatusCode.BAD_REQUEST:
      return 'BAD_REQUEST';
    case HttpStatusCode.UNAUTHORIZED:
      return 'UNAUTHORIZED';
    case HttpStatusCode.FORBIDDEN:
      return 'FORBIDDEN';
    case HttpStatusCode.NOT_FOUND:
      return 'NOT_FOUND';
    case HttpStatusCode.METHOD_NOT_ALLOWED:
      return 'METHOD_NOT_ALLOWED';
    case HttpStatusCode.CONFLICT:
      return 'CONFLICT';
    case HttpStatusCode.UNPROCESSABLE_ENTITY:
      return 'VALIDATION_ERROR';
    case HttpStatusCode.TOO_MANY_REQUESTS:
      return 'RATE_LIMITED';
    case HttpStatusCode.INTERNAL_SERVER_ERROR:
      return 'INTERNAL_ERROR';
    case HttpStatusCode.BAD_GATEWAY:
      return 'BAD_GATEWAY';
    case HttpStatusCode.SERVICE_UNAVAILABLE:
      return 'SERVICE_UNAVAILABLE';
    case HttpStatusCode.GATEWAY_TIMEOUT:
      return 'GATEWAY_TIMEOUT';
    default:
      return `HTTP_${status}`;
  }
}

/**
 * Handle fetch errors (network, timeout, etc.)
 */
export function handleFetchError(error: any, request?: Request): Error {
  const requestId = request?.headers.get('X-Request-ID') || undefined;

  // Handle timeout errors
  if (error.name === 'AbortError') {
    return new TimeoutError(30000, 'Request timed out');
  }

  // Handle network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return new NetworkError('Network request failed', error);
  }

  // Handle other fetch errors
  if (error instanceof Error) {
    return error;
  }

  // Fallback for unknown errors
  return new Error(`Unknown error: ${String(error)}`);
}

/**
 * Default error interceptor instance
 */
export const errorInterceptor = createErrorInterceptor();

/**
 * Enhanced error interceptor with custom handlers
 */
export const enhancedErrorInterceptor = createErrorInterceptor({
  errorHandlers: {
    [HttpStatusCode.UNAUTHORIZED]: (error, request) => {
      // Handle auth errors
      console.warn('Authentication required');
      // Could trigger login flow here
      return error;
    },
    [HttpStatusCode.FORBIDDEN]: (error, request) => {
      // Handle permission errors
      console.warn('Insufficient permissions');
      return error;
    },
    [HttpStatusCode.TOO_MANY_REQUESTS]: (error, request) => {
      // Handle rate limiting
      console.warn('Rate limited - backing off');
      return error;
    },
    [HttpStatusCode.SERVICE_UNAVAILABLE]: (error, request) => {
      // Handle service unavailable
      console.warn('Service temporarily unavailable');
      return error;
    }
  },
  onError: (error, request) => {
    // Enhanced error logging
    const context = {
      error: {
        name: error.name,
        message: error.message,
        status: error.status || error.statusCode,
        code: error.errorCode || error.code
      },
      request: request ? {
        method: request.method,
        url: request.url,
        requestId: request.headers.get('X-Request-ID')
      } : undefined,
      timestamp: new Date().toISOString()
    };

    console.error('🚨 API Error:', context);

    // Send to error tracking service in production
    if (process.env.NODE_ENV === 'production') {
      // Example: Sentry, LogRocket, etc.
      // errorTracker.captureException(error, context);
    }
  }
});

/**
 * Create user-friendly error messages
 */
export function createUserFriendlyError(error: any): string {
  if (isApiError(error)) {
    switch (error.statusCode) {
      case HttpStatusCode.BAD_REQUEST:
        return 'The request was invalid. Please check your input and try again.';
      case HttpStatusCode.UNAUTHORIZED:
        return 'You need to log in to access this resource.';
      case HttpStatusCode.FORBIDDEN:
        return 'You don\'t have permission to access this resource.';
      case HttpStatusCode.NOT_FOUND:
        return 'The requested resource was not found.';
      case HttpStatusCode.CONFLICT:
        return 'This action conflicts with the current state. Please refresh and try again.';
      case HttpStatusCode.UNPROCESSABLE_ENTITY:
        return 'The data provided is invalid. Please check your input.';
      case HttpStatusCode.TOO_MANY_REQUESTS:
        return 'Too many requests. Please wait a moment and try again.';
      case HttpStatusCode.INTERNAL_SERVER_ERROR:
        return 'An internal server error occurred. Please try again later.';
      case HttpStatusCode.SERVICE_UNAVAILABLE:
        return 'The service is temporarily unavailable. Please try again later.';
      default:
        return error.message || 'An unexpected error occurred.';
    }
  }

  if (error instanceof NetworkError) {
    return 'Network error. Please check your connection and try again.';
  }

  if (error instanceof TimeoutError) {
    return 'The request timed out. Please try again.';
  }

  return 'An unexpected error occurred. Please try again.';
}

/**
 * Check if error is recoverable (user can retry)
 */
export function isRecoverableError(error: any): boolean {
  if (isApiError(error)) {
    // Client errors (4xx) are usually not recoverable by retrying
    if (error.statusCode >= 400 && error.statusCode < 500) {
      // Except for these cases
      return error.statusCode === HttpStatusCode.TOO_MANY_REQUESTS;
    }
    
    // Server errors (5xx) are usually recoverable
    return error.statusCode >= 500;
  }

  // Network and timeout errors are usually recoverable
  return error instanceof NetworkError || error instanceof TimeoutError;
}

/**
 * Extract validation errors from error response
 */
export function extractValidationErrors(error: any): Array<{ field: string; message: string }> {
  if (error instanceof ValidationApiError) {
    return error.validationErrors.map(ve => ({
      field: ve.field,
      message: ve.message
    }));
  }

  return [];
}

/**
 * Get error severity level
 */
export function getErrorSeverity(error: any): 'low' | 'medium' | 'high' | 'critical' {
  if (isApiError(error)) {
    if (error.statusCode >= 500) {
      return 'critical';
    }
    if (error.statusCode === HttpStatusCode.UNAUTHORIZED || error.statusCode === HttpStatusCode.FORBIDDEN) {
      return 'high';
    }
    if (error.statusCode === HttpStatusCode.NOT_FOUND || error.statusCode === HttpStatusCode.CONFLICT) {
      return 'medium';
    }
    return 'low';
  }

  if (error instanceof NetworkError) {
    return 'high';
  }

  if (error instanceof TimeoutError) {
    return 'medium';
  }

  return 'medium';
}