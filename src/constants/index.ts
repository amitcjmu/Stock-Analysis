/**
 * Frontend constants module for UI constants, flow states, and configuration values.
 * Provides centralized constants for consistent UI behavior and styling.
 */

export * from './uiConstants';
export * from './flowStates';
export * from './apiEndpoints';
export * from './colors';
export * from './sizing';
export * from './routes';
export * from './permissions';
export * from './validation';
export * from './errorMessages';
export * from './features';

// Re-export commonly used constants
export {
  FLOW_STATUSES,
  FLOW_PHASES,
  FLOW_TYPES,
  UI_COLORS,
  BREAKPOINTS,
  API_ENDPOINTS,
  ROUTES,
  PERMISSIONS,
  ERROR_MESSAGES
} from './uiConstants';