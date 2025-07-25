/**
 * Shared API Type Definitions
 *
 * Standardized API interfaces to replace any types in API response handling
 */

/**
 * Standard API response wrapper
 */
export interface ApiResponse<TData = unknown, TError = ApiError> {
  /** Response data payload */
  data: TData;
  /** Error information if request failed */
  error?: TError;
  /** Response metadata */
  meta?: ResponseMetadata;
  /** Response success status */
  success: boolean;
}

/**
 * Standard API error structure
 */
export interface ApiError {
  /** Error code for programmatic handling */
  code: string;
  /** Human-readable error message */
  message: string;
  /** Additional error details */
  details?: Record<string, unknown>;
  /** Error stack trace (development only) */
  stack?: string;
  /** Correlation ID for tracing */
  correlationId?: string;
}

/**
 * API response metadata
 */
export interface ResponseMetadata {
  /** Request timestamp */
  timestamp: string;
  /** Processing duration in milliseconds */
  duration: number;
  /** API version that processed the request */
  version: string;
  /** Pagination information for list endpoints */
  pagination?: {
    page: number;
    size: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  /** Rate limiting information */
  rateLimit?: {
    limit: number;
    remaining: number;
    resetTime: string;
  };
}
