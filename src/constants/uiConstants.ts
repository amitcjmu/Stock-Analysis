/**
 * UI constants for consistent styling and behavior.
 * Central location for all UI-related constants and configuration.
 */

// Export all constants for easy access
export * from './flowStates';

// Animation and timing constants
export const ANIMATIONS = {
  DURATION: {
    FAST: 150,
    NORMAL: 300,
    SLOW: 500,
    VERY_SLOW: 1000
  },
  EASING: {
    EASE_IN: 'ease-in',
    EASE_OUT: 'ease-out',
    EASE_IN_OUT: 'ease-in-out',
    BOUNCE: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)'
  }
} as const;

// Z-index layers
export const Z_INDEX = {
  DROPDOWN: 1000,
  STICKY: 1020,
  FIXED: 1030,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOOLTIP: 1070,
  NOTIFICATION: 1080
} as const;

// Component sizes
export const COMPONENT_SIZES = {
  BUTTON: {
    SMALL: 'sm',
    MEDIUM: 'md',
    LARGE: 'lg'
  },
  INPUT: {
    SMALL: 'sm',
    MEDIUM: 'md',
    LARGE: 'lg'
  },
  CARD: {
    COMPACT: 'compact',
    NORMAL: 'normal',
    SPACIOUS: 'spacious'
  }
} as const;

// Loading states
export const LOADING_STATES = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error'
} as const;

// Form states
export const FORM_STATES = {
  PRISTINE: 'pristine',
  DIRTY: 'dirty',
  SUBMITTING: 'submitting',
  SUBMITTED: 'submitted',
  ERROR: 'error'
} as const;

// Table configuration
export const TABLE_CONFIG = {
  DEFAULT_PAGE_SIZE: 50,
  PAGE_SIZE_OPTIONS: [25, 50, 100, 200],
  MAX_PAGE_SIZE: 1000,
  SORT_DIRECTIONS: ['asc', 'desc'] as const
} as const;

// File upload constants
export const FILE_UPLOAD = {
  MAX_SIZE: {
    IMAGE: 5 * 1024 * 1024, // 5MB
    DOCUMENT: 10 * 1024 * 1024, // 10MB
    CSV: 50 * 1024 * 1024, // 50MB
    GENERAL: 100 * 1024 * 1024 // 100MB
  },
  ALLOWED_TYPES: {
    IMAGE: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    DOCUMENT: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    CSV: ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    JSON: ['application/json', 'text/json']
  },
  CHUNK_SIZE: 1024 * 1024 // 1MB chunks for large file uploads
} as const;

// Notification types and durations
export const NOTIFICATIONS = {
  TYPES: {
    SUCCESS: 'success',
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
  },
  DURATION: {
    SHORT: 3000,
    MEDIUM: 5000,
    LONG: 8000,
    PERSISTENT: 0 // Don't auto-dismiss
  },
  POSITIONS: {
    TOP_RIGHT: 'top-right',
    TOP_LEFT: 'top-left',
    BOTTOM_RIGHT: 'bottom-right',
    BOTTOM_LEFT: 'bottom-left',
    TOP_CENTER: 'top-center',
    BOTTOM_CENTER: 'bottom-center'
  }
} as const;

// Progress indicators
export const PROGRESS = {
  TYPES: {
    LINEAR: 'linear',
    CIRCULAR: 'circular',
    STEP: 'step'
  },
  VARIANTS: {
    DETERMINATE: 'determinate',
    INDETERMINATE: 'indeterminate'
  }
} as const;

// Modal configurations
export const MODAL_CONFIG = {
  SIZES: {
    SMALL: 'sm',
    MEDIUM: 'md',
    LARGE: 'lg',
    EXTRA_LARGE: 'xl',
    FULL_SCREEN: 'full'
  },
  CLOSE_METHODS: {
    OVERLAY: 'overlay',
    ESCAPE: 'escape',
    BUTTON: 'button'
  }
} as const;

// Search and filtering
export const SEARCH_CONFIG = {
  DEBOUNCE_DELAY: 300,
  MIN_SEARCH_LENGTH: 2,
  MAX_RECENT_SEARCHES: 10,
  OPERATORS: {
    EQUALS: 'eq',
    NOT_EQUALS: 'ne',
    CONTAINS: 'contains',
    STARTS_WITH: 'starts_with',
    ENDS_WITH: 'ends_with',
    GREATER_THAN: 'gt',
    LESS_THAN: 'lt',
    BETWEEN: 'between'
  }
} as const;

// Date and time formats
export const DATE_FORMATS = {
  SHORT: 'MM/dd/yyyy',
  MEDIUM: 'MMM dd, yyyy',
  LONG: 'MMMM dd, yyyy',
  ISO: 'yyyy-MM-dd',
  DATETIME: 'MM/dd/yyyy HH:mm',
  DATETIME_LONG: 'MMMM dd, yyyy HH:mm:ss',
  TIME: 'HH:mm',
  TIME_WITH_SECONDS: 'HH:mm:ss'
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
  LANGUAGE: 'language',
  SIDEBAR_STATE: 'sidebar_state',
  TABLE_SETTINGS: 'table_settings',
  RECENT_SEARCHES: 'recent_searches',
  FLOW_CONTEXT: 'flow_context',
  TENANT_CONTEXT: 'tenant_context'
} as const;

// Theme constants
export const THEME = {
  MODES: {
    LIGHT: 'light',
    DARK: 'dark',
    SYSTEM: 'system'
  },
  STORAGE_KEY: 'theme-preference'
} as const;

// Accessibility constants
export const A11Y = {
  ARIA_LABELS: {
    LOADING: 'Loading content',
    ERROR: 'Error message',
    SUCCESS: 'Success message',
    WARNING: 'Warning message',
    INFO: 'Information message',
    CLOSE: 'Close',
    MENU: 'Main menu',
    SEARCH: 'Search',
    FILTER: 'Filter options',
    SORT: 'Sort options'
  },
  ROLES: {
    BUTTON: 'button',
    LINK: 'link',
    MENU: 'menu',
    MENUITEM: 'menuitem',
    TAB: 'tab',
    TABPANEL: 'tabpanel',
    DIALOG: 'dialog',
    ALERT: 'alert',
    STATUS: 'status'
  }
} as const;

// Performance constants
export const PERFORMANCE = {
  DEBOUNCE_DELAY: 300,
  THROTTLE_DELAY: 100,
  VIRTUAL_SCROLL_THRESHOLD: 100,
  LAZY_LOAD_THRESHOLD: 50,
  CACHE_TTL: 5 * 60 * 1000, // 5 minutes
  MAX_CACHE_SIZE: 100
} as const;

// Feature flags
export const FEATURE_FLAGS = {
  BETA_FEATURES: 'beta_features',
  ADVANCED_SEARCH: 'advanced_search',
  BULK_OPERATIONS: 'bulk_operations',
  REAL_TIME_UPDATES: 'real_time_updates',
  DARK_MODE: 'dark_mode',
  ANALYTICS: 'analytics'
} as const;

// Default configurations
export const DEFAULTS = {
  PAGINATION: {
    PAGE: 1,
    PAGE_SIZE: 50,
    SHOW_SIZE_SELECTOR: true,
    SHOW_QUICK_JUMPER: false
  },
  FORM: {
    SUBMIT_ON_ENTER: true,
    VALIDATE_ON_BLUR: true,
    VALIDATE_ON_CHANGE: false,
    SHOW_ASTERISK_FOR_REQUIRED: true
  },
  TABLE: {
    SHOW_HEADER: true,
    SHOW_FOOTER: false,
    SELECTABLE: false,
    SORTABLE: true,
    FILTERABLE: false,
    RESIZABLE: false
  }
} as const;