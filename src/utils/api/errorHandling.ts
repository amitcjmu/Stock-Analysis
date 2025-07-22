/**
 * API error handling utilities.
 * Provides consistent error handling patterns and error transformations.
 */

import type {
  ApiErrorType,
  NetworkError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  ServerError,
  ApiError
} from './apiTypes';

export function createApiError(
  status: number,
  response: unknown,
  context: { url: string; method: string; response?: unknown }
): ApiErrorType {
  const responseObj = response as Record<string, unknown>;
  
  if (status >= 500) {
    return {
      type: 'server',
      message: (responseObj?.message as string) || 'Internal server error',
      code: (responseObj?.error_code as string) || `HTTP_${status}`,
      status,
      errorId: (responseObj?.meta as Record<string, unknown>)?.error_id as string,
      correlationId: (responseObj?.correlationId as string)
    } as ServerError;
  }
  
  if (status === 401) {
    return {
      type: 'authentication',
      message: (responseObj?.message as string) || 'Authentication required',
      code: (responseObj?.error_code as string) || 'UNAUTHORIZED',
      reason: determineAuthReason(responseObj),
      correlationId: (responseObj?.correlationId as string)
    } as AuthenticationError;
  }
  
  if (status === 403) {
    return {
      type: 'authorization',
      message: (responseObj?.message as string) || 'Access forbidden',
      code: (responseObj?.error_code as string) || 'FORBIDDEN',
      requiredPermissions: responseObj?.required_permissions as string[],
      userPermissions: responseObj?.user_permissions as string[],
      resource: responseObj?.resource as string,
      correlationId: (responseObj?.correlationId as string)
    } as AuthorizationError;
  }
  
  if (status === 422) {
    return {
      type: 'validation',
      message: (responseObj?.message as string) || 'Validation failed',
      code: (responseObj?.error_code as string) || 'VALIDATION_ERROR',
      field: responseObj?.field as string,
      value: responseObj?.value,
      errors: (responseObj?.errors as ApiError[]) || [],
      correlationId: (responseObj?.correlationId as string)
    } as ValidationError;
  }
  
  return {
    type: 'network',
    message: (responseObj?.message as string) || `HTTP ${status} error`,
    code: (responseObj?.error_code as string) || `HTTP_${status}`,
    url: context.url,
    method: context.method,
    status,
    response: context.response,
    correlationId: (responseObj?.correlationId as string)
  } as NetworkError;
}

function determineAuthReason(response: Record<string, unknown> | undefined): 'token_expired' | 'invalid_credentials' | 'missing_token' {
  const code = (response?.error_code as string)?.toLowerCase();
  
  if (code?.includes('expired')) return 'token_expired';
  if (code?.includes('invalid')) return 'invalid_credentials';
  return 'missing_token';
}

export function handleApiError(error: ApiErrorType): {
  userMessage: string;
  technicalMessage: string;
  shouldRetry: boolean;
  actions: string[];
} {
  switch (error.type) {
    case 'authentication':
      return {
        userMessage: 'Please sign in to continue',
        technicalMessage: error.message,
        shouldRetry: false,
        actions: ['redirect_to_login', 'refresh_token']
      };
    
    case 'authorization':
      return {
        userMessage: 'You do not have permission to perform this action',
        technicalMessage: error.message,
        shouldRetry: false,
        actions: ['contact_admin', 'request_permission']
      };
    
    case 'validation':
      return {
        userMessage: 'Please check your input and try again',
        technicalMessage: error.message,
        shouldRetry: false,
        actions: ['fix_validation_errors']
      };
    
    case 'network':
      return {
        userMessage: 'Network error. Please check your connection',
        technicalMessage: error.message,
        shouldRetry: true,
        actions: ['retry_request', 'check_connection']
      };
    
    case 'server':
      return {
        userMessage: 'Server error. Please try again later',
        technicalMessage: error.message,
        shouldRetry: true,
        actions: ['retry_request', 'contact_support']
      };
    
    default:
      return {
        userMessage: 'An unexpected error occurred',
        technicalMessage: 'Unknown error type',
        shouldRetry: false,
        actions: ['refresh_page', 'contact_support']
      };
  }
}

export function isRetryableError(error: ApiErrorType): boolean {
  return ['network', 'server'].includes(error.type) && 
    (!('status' in error) || error.status >= 500 || error.status === 429);
}

export function getErrorMessage(error: ApiErrorType): string {
  return handleApiError(error).userMessage;
}

export function getErrorActions(error: ApiErrorType): string[] {
  return handleApiError(error).actions;
}