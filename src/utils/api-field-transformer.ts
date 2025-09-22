/**
 * API Field Transformer Utility (LEGACY - NO-OP)
 *
 * NOTE: As of Aug 2025, frontend now uses snake_case to match backend.
 * This module is retained only for backward compatibility.
 * All functions return input unchanged to avoid unintended transformations.
 *
 * DEPRECATED: Do not use in new code. Will be removed in future versions.
 */

import SecureLogger from './secureLogger';

/**
 * NO-OP: Returns response unchanged (frontend now uses snake_case)
 * @deprecated Use raw response directly
 */
export function transformFlowResponse<T>(response: T): T {
  SecureLogger.debug('transformFlowResponse called (no-op) - frontend now uses snake_case');
  return response;
}

/**
 * NO-OP: Returns data unchanged (frontend now uses snake_case)
 * @deprecated Use raw data directly
 */
export function ensureFrontendFormat<T>(data: T): T {
  SecureLogger.debug('ensureFrontendFormat called (no-op) - frontend now uses snake_case');
  return data;
}

/**
 * NO-OP: Returns data unchanged (frontend now uses snake_case)
 * @deprecated Use raw data directly
 */
export function transformRequestData<T>(data: T): T {
  SecureLogger.debug('transformRequestData called (no-op) - frontend now uses snake_case');
  return data;
}

/**
 * NO-OP: Returns object unchanged
 * @deprecated No transformation needed
 */
export function snakeToCamelCase<T>(obj: T): T {
  return obj;
}

/**
 * NO-OP: Returns object unchanged
 * @deprecated No transformation needed
 */
export function camelToSnakeCase<T>(obj: T): T {
  return obj;
}

/**
 * NO-OP: Returns string unchanged
 * @deprecated No transformation needed
 */
export function toCamelCase(str: string): string {
  return str;
}

/**
 * NO-OP: Returns string unchanged
 * @deprecated No transformation needed
 */
export function toSnakeCase(str: string): string {
  return str;
}

/**
 * Check if an object has the expected flow properties
 * Checks for either snake_case or legacy camelCase for backward compatibility
 */
export function isValidFlowObject(obj: unknown): boolean {
  if (!obj || typeof obj !== 'object') {
    return false;
  }
  const record = obj as Record<string, unknown>;
  // Check for snake_case (current) or camelCase (legacy)
  const hasFlowId = record.flow_id || record.flowId;
  const hasStatus = record.status;
  return Boolean(hasFlowId && hasStatus);
}

/**
 * Get flow ID from object (handles both snake_case and legacy camelCase)
 */
export function getFlowId(obj: unknown): string | null {
  if (!obj || typeof obj !== 'object') {
    return null;
  }
  const record = obj as Record<string, unknown>;
  // Prefer snake_case, fallback to legacy camelCase
  return (record.flow_id as string) || (record.flowId as string) || null;
}

/**
 * Get flow status safely with null checks
 */
export function getFlowStatus(obj: unknown): string {
  if (!obj || typeof obj !== 'object') {
    return 'unknown';
  }
  const record = obj as Record<string, unknown>;
  return (record.status as string) || 'idle';
}

/**
 * Safe property accessor that tries both snake_case and legacy camelCase
 */
export function safeGetProperty(obj: unknown, key: string): unknown {
  if (!obj || typeof obj !== 'object') {
    return undefined;
  }

  const record = obj as Record<string, unknown>;

  // Try the key as-is first
  if (Object.prototype.hasOwnProperty.call(record, key)) {
    return record[key];
  }

  // Try converting between snake_case and camelCase for backward compatibility
  const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
  if (Object.prototype.hasOwnProperty.call(record, snakeKey)) {
    return record[snakeKey];
  }

  return undefined;
}

// Export utility functions for backward compatibility
export {
  isValidFlowObject,
  getFlowId,
  getFlowStatus,
  safeGetProperty
};
