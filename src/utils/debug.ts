/**
 * Debug Logging Utility
 *
 * Per GPT5 review: Wrap console logging with NODE_ENV checks to prevent
 * production info leakage and logging noise.
 *
 * Usage:
 *   import { debugLog, debugWarn, debugError } from '@/utils/debug';
 *   debugLog('My debug message', { data });
 *   debugWarn('Warning message');
 *   debugError('Error message', error);
 */

/**
 * Check if debug logging is enabled.
 * Enabled in development or when DEBUG env var is explicitly set.
 */
const isDebugEnabled = (): boolean => {
  // Always disable in production unless DEBUG flag explicitly set
  if (process.env.NODE_ENV === 'production') {
    return process.env.NEXT_PUBLIC_DEBUG === 'true';
  }
  // Enable in development by default
  return true;
};

/**
 * Debug log (console.log wrapper with environment check)
 */
export const debugLog = (...args: unknown[]): void => {
  if (isDebugEnabled()) {
    console.log('[DEBUG]', ...args);
  }
};

/**
 * Debug warning (console.warn wrapper with environment check)
 */
export const debugWarn = (...args: unknown[]): void => {
  if (isDebugEnabled()) {
    console.warn('[DEBUG:WARN]', ...args);
  }
};

/**
 * Debug error (console.error wrapper)
 * Errors are ALWAYS logged (even in production) but with sanitized context
 */
export const debugError = (...args: unknown[]): void => {
  // Always log errors, but prefix with DEBUG in dev mode
  if (isDebugEnabled()) {
    console.error('[DEBUG:ERROR]', ...args);
  } else {
    // In production, log errors but sanitize potentially sensitive data
    const sanitizedArgs = args.map(arg => {
      if (arg instanceof Error) {
        return `${arg.name}: ${arg.message}`;
      }
      if (typeof arg === 'object' && arg !== null) {
        // Don't log full objects in production (may contain sensitive data)
        return '[Object]';
      }
      return arg;
    });
    console.error('[ERROR]', ...sanitizedArgs);
  }
};

/**
 * Debug info (console.info wrapper with environment check)
 */
export const debugInfo = (...args: unknown[]): void => {
  if (isDebugEnabled()) {
    console.info('[DEBUG:INFO]', ...args);
  }
};

/**
 * Debug table (console.table wrapper with environment check)
 */
export const debugTable = (data: unknown): void => {
  if (isDebugEnabled() && console.table) {
    console.table(data);
  }
};

/**
 * Debug group (console.group wrapper with environment check)
 */
export const debugGroup = (label: string): void => {
  if (isDebugEnabled() && console.group) {
    console.group(`[DEBUG] ${label}`);
  }
};

/**
 * Debug group end (console.groupEnd wrapper with environment check)
 */
export const debugGroupEnd = (): void => {
  if (isDebugEnabled() && console.groupEnd) {
    console.groupEnd();
  }
};
