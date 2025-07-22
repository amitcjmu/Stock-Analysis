/**
 * Validation constants and rules
 */

export const VALIDATION_RULES = {
  // String validation
  STRING: {
    MIN_LENGTH: 1,
    MAX_LENGTH: 255,
    MAX_LONG_TEXT: 5000,
    MAX_NAME_LENGTH: 100,
    MAX_DESCRIPTION_LENGTH: 500,
    MAX_URL_LENGTH: 2048
  },
  
  // Number validation
  NUMBER: {
    MIN_PORT: 1,
    MAX_PORT: 65535,
    MIN_PERCENTAGE: 0,
    MAX_PERCENTAGE: 100,
    MIN_COUNT: 0,
    MAX_COUNT: Number.MAX_SAFE_INTEGER
  },
  
  // File validation
  FILE: {
    MAX_SIZE: 100 * 1024 * 1024, // 100MB
    MAX_IMAGE_SIZE: 5 * 1024 * 1024, // 5MB
    MAX_CSV_SIZE: 50 * 1024 * 1024, // 50MB
    MAX_JSON_SIZE: 10 * 1024 * 1024, // 10MB
    ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    ALLOWED_DOCUMENT_TYPES: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    ALLOWED_DATA_TYPES: ['text/csv', 'application/json', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
  },
  
  // Password validation
  PASSWORD: {
    MIN_LENGTH: 8,
    MAX_LENGTH: 128,
    REQUIRE_UPPERCASE: true,
    REQUIRE_LOWERCASE: true,
    REQUIRE_NUMBER: true,
    REQUIRE_SPECIAL: true,
    SPECIAL_CHARS: '!@#$%^&*()_+-=[]{}|;:,.<>?'
  },
  
  // Email validation
  EMAIL: {
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    MAX_LENGTH: 254
  },
  
  // Username validation
  USERNAME: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 30,
    PATTERN: /^[a-zA-Z0-9_-]+$/,
    RESERVED_WORDS: ['admin', 'root', 'system', 'user', 'test']
  },
  
  // IP address validation
  IP: {
    IPV4_PATTERN: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
    IPV6_PATTERN: /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/,
    CIDR_PATTERN: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:3[0-2]|[1-2]?[0-9])$/
  },
  
  // Date validation
  DATE: {
    MIN_YEAR: 1900,
    MAX_YEAR: 2100,
    DATE_FORMAT: 'YYYY-MM-DD',
    DATETIME_FORMAT: 'YYYY-MM-DD HH:mm:ss'
  },
  
  // Array validation
  ARRAY: {
    MIN_ITEMS: 0,
    MAX_ITEMS: 1000,
    MAX_TAGS: 20,
    MAX_CATEGORIES: 10
  }
} as const;

// Validation messages
export const VALIDATION_MESSAGES = {
  REQUIRED: 'This field is required',
  MIN_LENGTH: (min: number) => `Minimum length is ${min} characters`,
  MAX_LENGTH: (max: number) => `Maximum length is ${max} characters`,
  MIN_VALUE: (min: number) => `Minimum value is ${min}`,
  MAX_VALUE: (max: number) => `Maximum value is ${max}`,
  INVALID_EMAIL: 'Please enter a valid email address',
  INVALID_URL: 'Please enter a valid URL',
  INVALID_PHONE: 'Please enter a valid phone number',
  INVALID_DATE: 'Please enter a valid date',
  INVALID_TIME: 'Please enter a valid time',
  INVALID_NUMBER: 'Please enter a valid number',
  INVALID_INTEGER: 'Please enter a whole number',
  INVALID_PERCENTAGE: 'Please enter a value between 0 and 100',
  INVALID_IP: 'Please enter a valid IP address',
  INVALID_PORT: 'Please enter a valid port number (1-65535)',
  PASSWORD_TOO_SHORT: `Password must be at least ${VALIDATION_RULES.PASSWORD.MIN_LENGTH} characters`,
  PASSWORD_TOO_LONG: `Password must be no more than ${VALIDATION_RULES.PASSWORD.MAX_LENGTH} characters`,
  PASSWORD_REQUIRES_UPPERCASE: 'Password must contain at least one uppercase letter',
  PASSWORD_REQUIRES_LOWERCASE: 'Password must contain at least one lowercase letter',
  PASSWORD_REQUIRES_NUMBER: 'Password must contain at least one number',
  PASSWORD_REQUIRES_SPECIAL: 'Password must contain at least one special character',
  USERNAME_INVALID: 'Username can only contain letters, numbers, underscores, and hyphens',
  USERNAME_RESERVED: 'This username is reserved',
  FILE_TOO_LARGE: (maxSize: number) => `File size must not exceed ${maxSize / 1024 / 1024}MB`,
  FILE_TYPE_NOT_ALLOWED: 'This file type is not allowed',
  ARRAY_TOO_MANY: (max: number) => `Maximum ${max} items allowed`,
  DUPLICATE_VALUE: 'This value already exists',
  FIELD_MISMATCH: 'Fields do not match',
  INVALID_FORMAT: 'Invalid format',
  CUSTOM: (message: string) => message
} as const;

// Common regex patterns
export const VALIDATION_PATTERNS = {
  EMAIL: VALIDATION_RULES.EMAIL.PATTERN,
  URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
  PHONE: /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{4,6}$/,
  ALPHANUMERIC: /^[a-zA-Z0-9]+$/,
  ALPHABETIC: /^[a-zA-Z]+$/,
  NUMERIC: /^[0-9]+$/,
  DECIMAL: /^-?\d+(\.\d+)?$/,
  HEX_COLOR: /^#?([a-fA-F0-9]{6}|[a-fA-F0-9]{3})$/,
  SLUG: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
  UUID: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
} as const;