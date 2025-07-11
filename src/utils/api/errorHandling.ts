/**
 * API error handling utilities.
 * Provides consistent error handling patterns and error transformations.
 */

import {
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
  response: any,
  context: { url: string; method: string; response?: any }
): ApiErrorType {
  const timestamp = new Date().toISOString();
  
  if (status >= 500) {
    return {
      type: 'server',
      message: response?.message || 'Internal server error',
      code: response?.error_code || `HTTP_${status}`,
      status,
      errorId: response?.meta?.error_id,
      timestamp
    } as ServerError;
  }
  
  if (status === 401) {
    return {
      type: 'authentication',
      message: response?.message || 'Authentication required',
      code: response?.error_code || 'UNAUTHORIZED',
      reason: determineAuthReason(response),
      timestamp
    } as AuthenticationError;
  }
  
  if (status === 403) {
    return {
      type: 'authorization',
      message: response?.message || 'Access forbidden',
      code: response?.error_code || 'FORBIDDEN',
      requiredPermissions: response?.required_permissions,
      userPermissions: response?.user_permissions,
      resource: response?.resource,
      timestamp
    } as AuthorizationError;
  }
  
  if (status === 422) {
    return {
      type: 'validation',
      message: response?.message || 'Validation failed',
      code: response?.error_code || 'VALIDATION_ERROR',
      errors: response?.errors || [],
      timestamp
    } as ValidationError;
  }
  
  return {
    type: 'network',
    message: response?.message || `HTTP ${status} error`,
    code: response?.error_code || `HTTP_${status}`,
    url: context.url,
    method: context.method,
    status,
    response: context.response,
    timestamp
  } as NetworkError;
}

function determineAuthReason(response: any): 'token_expired' | 'invalid_credentials' | 'missing_token' {
  const code = response?.error_code?.toLowerCase();
  
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