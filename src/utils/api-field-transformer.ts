/**
 * API Field Transformer Utility
 *
 * CRITICAL: This utility addresses the #1 recurring bug in the codebase -
 * confusion between snake_case (backend) and camelCase (frontend) field names.
 *
 * Rules:
 * 1. Backend (Python/FastAPI): ALWAYS returns snake_case fields (e.g., flow_id, client_account_id)
 * 2. Frontend (TypeScript/React): ALWAYS uses camelCase fields internally (e.g., flowId, clientAccountId)
 * 3. Raw API Calls: Will receive snake_case and MUST transform to camelCase
 * 4. Type Definitions: Frontend interfaces should use camelCase ONLY
 */

import SecureLogger from './secureLogger';

// Field mapping for snake_case to camelCase transformation
const FIELD_MAPPINGS: Record<string, string> = {
  // Flow fields
  'flow_id': 'flowId',
  'client_account_id': 'clientAccountId',
  'engagement_id': 'engagementId',
  'current_phase': 'currentPhase',
  'progress_percentage': 'progressPercentage',
  'crew_results': 'crewResults',
  'phase_completion': 'phaseCompletion',
  'error_message': 'errorMessage',
  'created_at': 'createdAt',
  'updated_at': 'updatedAt',

  // Crew result fields
  'execution_time': 'executionTime',

  // Common fields
  'field_mappings': 'fieldMappings',
  'source_field': 'sourceField',
  'target_field': 'targetField',
  'confidence_score': 'confidenceScore',
  'mapping_type': 'mappingType',
  'transformation_rule': 'transformationRule',
  'cleaned_data': 'cleanedData',
  'applied_transformations': 'appliedTransformations',
  'quality_score': 'qualityScore',
  'validation_errors': 'validationErrors',
  'total_assets': 'totalAssets',
  'categorized_assets': 'categorizedAssets',
  'discovery_methods': 'discoveryMethods',
  'coverage_percentage': 'coveragePercentage',
  'last_updated': 'lastUpdated',
  'total_dependencies': 'totalDependencies',
  'dependency_types': 'dependencyTypes',
  'critical_paths': 'criticalPaths',
  'circular_dependencies': 'circularDependencies',
  'total_debt_score': 'totalDebtScore',
  'debt_categories': 'debtCategories',
  'critical_issues': 'criticalIssues',
  'remediation_effort_hours': 'remediationEffortHours',
  'agent_type': 'agentType',
  'insight_category': 'insightCategory',
  'created_at': 'createdAt',
  'agent_insights': 'agentInsights'
};

// Reverse mapping for camelCase to snake_case (for API requests)
const REVERSE_FIELD_MAPPINGS: Record<string, string> = Object.fromEntries(
  Object.entries(FIELD_MAPPINGS).map(([snake, camel]) => [camel, snake])
);

/**
 * Convert snake_case keys to camelCase keys recursively
 */
function snakeToCamelCase(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => snakeToCamelCase(item));
  }

  if (typeof obj === 'object') {
    const converted: any = {};

    for (const [key, value] of Object.entries(obj)) {
      const camelKey = FIELD_MAPPINGS[key] || toCamelCase(key);
      converted[camelKey] = snakeToCamelCase(value);
    }

    return converted;
  }

  return obj;
}

/**
 * Convert camelCase keys to snake_case keys recursively
 */
function camelToSnakeCase(obj: any): any {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(item => camelToSnakeCase(item));
  }

  if (typeof obj === 'object') {
    const converted: any = {};

    for (const [key, value] of Object.entries(obj)) {
      const snakeKey = REVERSE_FIELD_MAPPINGS[key] || toSnakeCase(key);
      converted[snakeKey] = camelToSnakeCase(value);
    }

    return converted;
  }

  return obj;
}

/**
 * Convert a string from snake_case to camelCase
 */
function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

/**
 * Convert a string from camelCase to snake_case
 */
function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

/**
 * Transform flow response from backend (snake_case) to frontend format (camelCase)
 * This is the main function to use when receiving flow data from APIs
 */
export function transformFlowResponse(response: any): any {
  if (!response) {
    return null;
  }

  try {
    const transformed = snakeToCamelCase(response);

    SecureLogger.debug('Flow response transformed from snake_case to camelCase', {
      originalKeys: Object.keys(response),
      transformedKeys: Object.keys(transformed)
    });

    return transformed;
  } catch (error) {
    SecureLogger.error('Failed to transform flow response', { error, response });
    return response; // Return original on error
  }
}

/**
 * Ensure data is in frontend format (camelCase) - auto-detects and transforms if needed
 * Use this when you're unsure if the data is already in camelCase or still in snake_case
 */
export function ensureFrontendFormat(data: any): any {
  if (!data || typeof data !== 'object') {
    return data;
  }

  // Check if data appears to be in snake_case format
  const hasSnakeCase = Object.keys(data).some(key => key.includes('_'));
  const hasCamelCase = Object.keys(data).some(key => /[a-z][A-Z]/.test(key));

  if (hasSnakeCase && !hasCamelCase) {
    // Data appears to be in snake_case, transform it
    SecureLogger.debug('Data detected as snake_case, transforming to camelCase', {
      keys: Object.keys(data).slice(0, 10) // Log first 10 keys for debugging
    });
    return transformFlowResponse(data);
  } else if (hasCamelCase) {
    // Data appears to already be in camelCase
    SecureLogger.debug('Data already in camelCase format', {
      keys: Object.keys(data).slice(0, 10)
    });
    return data;
  } else {
    // Ambiguous or no transformation needed
    return data;
  }
}

/**
 * Transform request data from frontend format (camelCase) to backend format (snake_case)
 * Use this when sending data to APIs
 */
export function transformRequestData(data: any): any {
  if (!data) {
    return data;
  }

  try {
    const transformed = camelToSnakeCase(data);

    SecureLogger.debug('Request data transformed from camelCase to snake_case', {
      originalKeys: Object.keys(data),
      transformedKeys: Object.keys(transformed)
    });

    return transformed;
  } catch (error) {
    SecureLogger.error('Failed to transform request data', { error, data });
    return data; // Return original on error
  }
}

/**
 * Check if an object has the expected flow properties
 * Helps identify if flow object is properly loaded
 */
export function isValidFlowObject(obj: any): boolean {
  if (!obj || typeof obj !== 'object') {
    return false;
  }

  // Check for either camelCase or snake_case flow ID
  const hasFlowId = obj.flowId || obj.flow_id;
  const hasStatus = obj.status;

  return Boolean(hasFlowId && hasStatus);
}

/**
 * Get flow ID from object (handles both camelCase and snake_case)
 */
export function getFlowId(obj: any): string | null {
  if (!obj || typeof obj !== 'object') {
    return null;
  }

  return obj.flowId || obj.flow_id || null;
}

/**
 * Get flow status safely with null checks
 */
export function getFlowStatus(obj: any): string {
  if (!obj || typeof obj !== 'object') {
    return 'unknown';
  }

  return obj.status || 'idle';
}

/**
 * Safe property accessor that tries both camelCase and snake_case variants
 */
export function safeGetProperty(obj: any, camelKey: string): any {
  if (!obj || typeof obj !== 'object') {
    return undefined;
  }

  // Try camelCase first
  if (obj.hasOwnProperty(camelKey)) {
    return obj[camelKey];
  }

  // Try snake_case variant
  const snakeKey = REVERSE_FIELD_MAPPINGS[camelKey] || toSnakeCase(camelKey);
  if (obj.hasOwnProperty(snakeKey)) {
    return obj[snakeKey];
  }

  return undefined;
}

// Export utility functions
export {
  snakeToCamelCase,
  camelToSnakeCase,
  toCamelCase,
  toSnakeCase,
  isValidFlowObject,
  getFlowId,
  getFlowStatus,
  safeGetProperty
};
