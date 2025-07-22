/**
 * Error message constants for consistent error handling
 */

export const ERROR_MESSAGES = {
  // Generic errors
  GENERIC: {
    UNKNOWN: 'An unexpected error occurred. Please try again.',
    NETWORK: 'Network error. Please check your connection and try again.',
    TIMEOUT: 'Request timed out. Please try again.',
    SERVER: 'Server error. Please try again later.',
    NOT_FOUND: 'The requested resource was not found.',
    FORBIDDEN: 'You do not have permission to perform this action.',
    UNAUTHORIZED: 'Please log in to continue.',
    BAD_REQUEST: 'Invalid request. Please check your input and try again.',
    CONFLICT: 'A conflict occurred. Please refresh and try again.',
    RATE_LIMITED: 'Too many requests. Please wait a moment and try again.'
  },
  
  // Authentication errors
  AUTH: {
    INVALID_CREDENTIALS: 'Invalid email or password.',
    ACCOUNT_LOCKED: 'Your account has been locked. Please contact support.',
    ACCOUNT_DISABLED: 'Your account has been disabled.',
    SESSION_EXPIRED: 'Your session has expired. Please log in again.',
    TOKEN_INVALID: 'Invalid authentication token.',
    TOKEN_EXPIRED: 'Your authentication token has expired.',
    PASSWORD_RESET_REQUIRED: 'Password reset required. Please check your email.',
    EMAIL_NOT_VERIFIED: 'Please verify your email address.',
    TWO_FACTOR_REQUIRED: 'Two-factor authentication required.',
    TWO_FACTOR_INVALID: 'Invalid two-factor authentication code.'
  },
  
  // Validation errors
  VALIDATION: {
    REQUIRED_FIELD: 'This field is required.',
    INVALID_FORMAT: 'Invalid format.',
    INVALID_LENGTH: 'Invalid length.',
    INVALID_TYPE: 'Invalid data type.',
    DUPLICATE_ENTRY: 'This entry already exists.',
    INVALID_REFERENCE: 'Invalid reference.',
    OUT_OF_RANGE: 'Value is out of allowed range.',
    PATTERN_MISMATCH: 'Value does not match required pattern.'
  },
  
  // Data operation errors
  DATA: {
    CREATE_FAILED: 'Failed to create record.',
    UPDATE_FAILED: 'Failed to update record.',
    DELETE_FAILED: 'Failed to delete record.',
    FETCH_FAILED: 'Failed to fetch data.',
    SAVE_FAILED: 'Failed to save changes.',
    LOAD_FAILED: 'Failed to load data.',
    IMPORT_FAILED: 'Failed to import data.',
    EXPORT_FAILED: 'Failed to export data.',
    PARSE_FAILED: 'Failed to parse data.',
    VALIDATION_FAILED: 'Data validation failed.'
  },
  
  // File operation errors
  FILE: {
    UPLOAD_FAILED: 'Failed to upload file.',
    DOWNLOAD_FAILED: 'Failed to download file.',
    SIZE_EXCEEDED: 'File size exceeds maximum allowed.',
    TYPE_NOT_ALLOWED: 'File type not allowed.',
    CORRUPT_FILE: 'File appears to be corrupted.',
    MISSING_FILE: 'Required file is missing.',
    READ_FAILED: 'Failed to read file.',
    WRITE_FAILED: 'Failed to write file.'
  },
  
  // Workflow errors
  WORKFLOW: {
    START_FAILED: 'Failed to start workflow.',
    EXECUTION_FAILED: 'Workflow execution failed.',
    ALREADY_RUNNING: 'Workflow is already running.',
    NOT_FOUND: 'Workflow not found.',
    INVALID_STATE: 'Workflow is in an invalid state.',
    TRANSITION_FAILED: 'Failed to transition workflow state.',
    DEPENDENCY_FAILED: 'Workflow dependency check failed.',
    TIMEOUT: 'Workflow execution timed out.',
    CANCELLED: 'Workflow was cancelled.',
    VALIDATION_FAILED: 'Workflow validation failed.'
  },
  
  // Agent errors
  AGENT: {
    NOT_AVAILABLE: 'Agent is not available.',
    EXECUTION_FAILED: 'Agent execution failed.',
    COMMUNICATION_FAILED: 'Failed to communicate with agent.',
    INVALID_RESPONSE: 'Invalid response from agent.',
    TIMEOUT: 'Agent request timed out.',
    OVERLOADED: 'Agent is currently overloaded.',
    NOT_CONFIGURED: 'Agent is not properly configured.',
    LEARNING_FAILED: 'Agent learning process failed.'
  },
  
  // Collection errors
  COLLECTION: {
    IMPORT_FAILED: 'Failed to import collection data.',
    MAPPING_FAILED: 'Failed to map fields.',
    VALIDATION_FAILED: 'Collection data validation failed.',
    PROCESSING_FAILED: 'Failed to process collection.',
    DUPLICATE_DATA: 'Duplicate data detected.',
    INCOMPLETE_DATA: 'Incomplete data provided.',
    FORMAT_ERROR: 'Invalid data format.'
  },
  
  // Discovery errors
  DISCOVERY: {
    SCAN_FAILED: 'Discovery scan failed.',
    ANALYSIS_FAILED: 'Discovery analysis failed.',
    CONNECTION_FAILED: 'Failed to connect to discovery source.',
    INSUFFICIENT_DATA: 'Insufficient data for discovery.',
    INVALID_CONFIGURATION: 'Invalid discovery configuration.'
  },
  
  // Permission errors
  PERMISSION: {
    INSUFFICIENT_PRIVILEGES: 'Insufficient privileges for this operation.',
    ROLE_NOT_ASSIGNED: 'Required role not assigned.',
    ACCESS_DENIED: 'Access denied.',
    RESOURCE_LOCKED: 'Resource is locked by another user.',
    OPERATION_NOT_ALLOWED: 'Operation not allowed.'
  }
} as const;

// Error codes for programmatic handling
export const ERROR_CODES = {
  // HTTP status codes
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
  
  // Custom error codes
  VALIDATION_ERROR: 1000,
  AUTHENTICATION_ERROR: 2000,
  AUTHORIZATION_ERROR: 3000,
  BUSINESS_LOGIC_ERROR: 4000,
  EXTERNAL_SERVICE_ERROR: 5000,
  DATA_INTEGRITY_ERROR: 6000,
  WORKFLOW_ERROR: 7000,
  AGENT_ERROR: 8000
} as const;

// Helper function to get user-friendly error message
export const getErrorMessage = (error: unknown): string => {
  if (typeof error === 'string') return error;
  if (error instanceof Error) return error.message;
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return String(error.message);
  }
  return ERROR_MESSAGES.GENERIC.UNKNOWN;
};