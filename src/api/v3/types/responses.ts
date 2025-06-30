/**
 * Response Types for API v3
 * Common response formats and error handling types
 */

// === Standard Response Wrappers ===

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  request_id: string;
  timestamp: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, any>;
  request_id: string;
  timestamp: string;
}

export interface ValidationErrorResponse {
  error: string;
  message: string;
  validation_errors: ValidationError[];
  request_id: string;
  timestamp: string;
}

export interface NotFoundErrorResponse {
  error: string;
  message: string;
  resource_type: string;
  resource_id: string;
  request_id: string;
  timestamp: string;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value?: any;
}

// === HTTP Status Code Types ===

export enum HttpStatusCode {
  OK = 200,
  CREATED = 201,
  ACCEPTED = 202,
  NO_CONTENT = 204,
  BAD_REQUEST = 400,
  UNAUTHORIZED = 401,
  FORBIDDEN = 403,
  NOT_FOUND = 404,
  METHOD_NOT_ALLOWED = 405,
  CONFLICT = 409,
  UNPROCESSABLE_ENTITY = 422,
  TOO_MANY_REQUESTS = 429,
  INTERNAL_SERVER_ERROR = 500,
  BAD_GATEWAY = 502,
  SERVICE_UNAVAILABLE = 503,
  GATEWAY_TIMEOUT = 504
}

// === Error Classes ===

export class ApiError extends Error {
  public readonly statusCode: number;
  public readonly errorCode: string;
  public readonly details?: Record<string, any>;
  public readonly requestId?: string;
  public readonly isApiError = true;

  constructor(
    statusCode: number,
    errorCode: string,
    message: string,
    details?: Record<string, any>,
    requestId?: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
    this.requestId = requestId;
  }

  static fromResponse(response: ErrorResponse, statusCode: number): ApiError {
    return new ApiError(
      statusCode,
      response.error,
      response.message,
      response.details,
      response.request_id
    );
  }
}

export class ValidationApiError extends ApiError {
  public readonly validationErrors: ValidationError[];

  constructor(
    message: string,
    validationErrors: ValidationError[],
    requestId?: string
  ) {
    super(HttpStatusCode.UNPROCESSABLE_ENTITY, 'VALIDATION_ERROR', message, undefined, requestId);
    this.name = 'ValidationApiError';
    this.validationErrors = validationErrors;
  }

  static fromResponse(response: ValidationErrorResponse): ValidationApiError {
    return new ValidationApiError(
      response.message,
      response.validation_errors,
      response.request_id
    );
  }
}

export class NotFoundApiError extends ApiError {
  public readonly resourceType: string;
  public readonly resourceId: string;

  constructor(
    resourceType: string,
    resourceId: string,
    message?: string,
    requestId?: string
  ) {
    super(
      HttpStatusCode.NOT_FOUND,
      'RESOURCE_NOT_FOUND',
      message || `${resourceType} with ID ${resourceId} not found`,
      { resource_type: resourceType, resource_id: resourceId },
      requestId
    );
    this.name = 'NotFoundApiError';
    this.resourceType = resourceType;
    this.resourceId = resourceId;
  }

  static fromResponse(response: NotFoundErrorResponse): NotFoundApiError {
    return new NotFoundApiError(
      response.resource_type,
      response.resource_id,
      response.message,
      response.request_id
    );
  }
}

export class NetworkError extends Error {
  public readonly isNetworkError = true;
  public readonly originalError?: Error;

  constructor(message: string, originalError?: Error) {
    super(message);
    this.name = 'NetworkError';
    this.originalError = originalError;
  }
}

export class TimeoutError extends Error {
  public readonly isTimeoutError = true;
  public readonly timeout: number;

  constructor(timeout: number, message?: string) {
    super(message || `Request timed out after ${timeout}ms`);
    this.name = 'TimeoutError';
    this.timeout = timeout;
  }
}

// === Response Type Guards ===

export function isApiError(error: any): error is ApiError {
  return error && typeof error === 'object' && error.isApiError === true;
}

export function isValidationApiError(error: any): error is ValidationApiError {
  return isApiError(error) && error.name === 'ValidationApiError';
}

export function isNotFoundApiError(error: any): error is NotFoundApiError {
  return isApiError(error) && error.name === 'NotFoundApiError';
}

export function isNetworkError(error: any): error is NetworkError {
  return error && typeof error === 'object' && error.isNetworkError === true;
}

export function isTimeoutError(error: any): error is TimeoutError {
  return error && typeof error === 'object' && error.isTimeoutError === true;
}

// === Response Processing Helpers ===

export interface ResponseProcessor<T> {
  process(data: any): T;
  validate?(data: T): boolean;
  transform?(data: T): T;
}

export function createResponseProcessor<T>(
  processor: (data: any) => T,
  validator?: (data: T) => boolean,
  transformer?: (data: T) => T
): ResponseProcessor<T> {
  return {
    process: processor,
    validate: validator,
    transform: transformer
  };
}

// === Success Response Helpers ===

export function isSuccessResponse<T>(response: any): response is ApiResponse<T> {
  return response && typeof response === 'object' && response.success === true;
}

export function isErrorResponse(response: any): response is ErrorResponse {
  return response && typeof response === 'object' && typeof response.error === 'string';
}

export function isValidationErrorResponse(response: any): response is ValidationErrorResponse {
  return isErrorResponse(response) && Array.isArray((response as any).validation_errors);
}

export function isNotFoundErrorResponse(response: any): response is NotFoundErrorResponse {
  return isErrorResponse(response) && 
         typeof (response as any).resource_type === 'string' && 
         typeof (response as any).resource_id === 'string';
}

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