/**
 * Color constants for consistent theming across the application
 */

export const UI_COLORS = {
  // Primary colors
  PRIMARY: '#3B82F6', // Blue
  PRIMARY_HOVER: '#2563EB',
  PRIMARY_LIGHT: '#DBEAFE',
  
  // Secondary colors
  SECONDARY: '#8B5CF6', // Purple
  SECONDARY_HOVER: '#7C3AED',
  SECONDARY_LIGHT: '#EDE9FE',
  
  // Success colors
  SUCCESS: '#10B981', // Green
  SUCCESS_HOVER: '#059669',
  SUCCESS_LIGHT: '#D1FAE5',
  
  // Warning colors
  WARNING: '#F59E0B', // Amber
  WARNING_HOVER: '#D97706',
  WARNING_LIGHT: '#FEF3C7',
  
  // Error colors
  ERROR: '#EF4444', // Red
  ERROR_HOVER: '#DC2626',
  ERROR_LIGHT: '#FEE2E2',
  
  // Info colors
  INFO: '#3B82F6', // Blue
  INFO_HOVER: '#2563EB',
  INFO_LIGHT: '#DBEAFE',
  
  // Neutral colors
  NEUTRAL: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827'
  },
  
  // Background colors
  BACKGROUND: {
    PRIMARY: '#FFFFFF',
    SECONDARY: '#F9FAFB',
    TERTIARY: '#F3F4F6'
  },
  
  // Border colors
  BORDER: {
    DEFAULT: '#E5E7EB',
    FOCUS: '#3B82F6',
    ERROR: '#EF4444'
  },
  
  // Text colors
  TEXT: {
    PRIMARY: '#111827',
    SECONDARY: '#6B7280',
    TERTIARY: '#9CA3AF',
    INVERSE: '#FFFFFF'
  }
} as const;

// Status colors for workflows
export const STATUS_COLORS = {
  PENDING: UI_COLORS.NEUTRAL[400],
  IN_PROGRESS: UI_COLORS.INFO,
  COMPLETED: UI_COLORS.SUCCESS,
  FAILED: UI_COLORS.ERROR,
  CANCELLED: UI_COLORS.NEUTRAL[500]
} as const;

// Semantic color mappings
export const SEMANTIC_COLORS = {
  DANGER: UI_COLORS.ERROR,
  WARNING: UI_COLORS.WARNING,
  SUCCESS: UI_COLORS.SUCCESS,
  INFO: UI_COLORS.INFO,
  DEFAULT: UI_COLORS.NEUTRAL[500]
} as const;