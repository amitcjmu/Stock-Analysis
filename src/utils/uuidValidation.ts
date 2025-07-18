/**
 * UUID Validation and Type Safety Utilities
 * 
 * Provides comprehensive UUID validation and type safety to prevent
 * character corruption issues in flow ID handling.
 */

// UUID validation regex
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

// Branded type for validated UUIDs
export type ValidatedUUID = string & { readonly __brand: unique symbol };

/**
 * Validates if a string is a proper UUID format
 */
export function isValidUUID(value: string): value is ValidatedUUID {
  return UUID_REGEX.test(value);
}

/**
 * Validates and returns a UUID, throwing if invalid
 */
export function validateUUID(value: string, context: string = 'UUID'): ValidatedUUID {
  if (!value) {
    throw new Error(`${context} is required`);
  }
  
  if (!isValidUUID(value)) {
    console.error(`❌ Invalid UUID detected in ${context}:`, {
      received: value,
      length: value.length,
      characters: value.split('').map((char, idx) => ({ idx, char, code: char.charCodeAt(0) }))
    });
    throw new Error(`${context} must be a valid UUID format: ${value}`);
  }
  
  return value as ValidatedUUID;
}

/**
 * Source object interface for flow ID extraction
 */
interface FlowIdSource {
  flow_id?: string;
  flowId?: string;
  id?: string;
}

/**
 * Type guard for flow ID source objects
 */
function isFlowIdSource(source: unknown): source is FlowIdSource {
  return (
    typeof source === 'object' &&
    source !== null &&
    ('flow_id' in source || 'flowId' in source || 'id' in source)
  );
}

/**
 * Safely extracts flow ID from various possible sources with validation
 */
export function extractFlowId(
  source: FlowIdSource | string,
  context: string = 'Flow ID'
): ValidatedUUID {
  let flowId: string;
  
  if (typeof source === 'string') {
    flowId = source;
  } else if (isFlowIdSource(source)) {
    // Try different possible field names
    flowId = source.flow_id || source.flowId || source.id || '';
  } else {
    throw new Error(`${context}: Invalid source type`);
  }
  
  return validateUUID(flowId, context);
}

/**
 * Creates a display-safe version of UUID for UI
 * Adds visual verification to catch corruption
 */
export function createDisplaySafeUUID(uuid: ValidatedUUID, options: {
  prefix?: boolean;
  length?: number;
  verify?: boolean;
} = {}): string {
  const { prefix = true, length = 8, verify = true } = options;
  
  if (verify) {
    // Re-validate to catch any corruption
    validateUUID(uuid, 'Display UUID');
  }
  
  const shortId = uuid.slice(0, length);
  
  // Add visual indicators to help spot corruption
  return prefix ? `ID:${shortId}...` : `${shortId}...`;
}

/**
 * Flow object interface for validation
 */
interface FlowObject extends FlowIdSource {
  master_flow_id?: string;
  [key: string]: unknown;
}

/**
 * Type guard for flow objects
 */
function isFlowObject(obj: unknown): obj is FlowObject {
  return typeof obj === 'object' && obj !== null && isFlowIdSource(obj);
}

/**
 * Flow validation result interface
 */
interface FlowValidationResult {
  flow_id: ValidatedUUID;
  validated: boolean;
  issues: string[];
}

/**
 * Deep validation for flow objects to ensure ID integrity
 */
export function validateFlowObject(
  flow: unknown,
  context: string = 'Flow object'
): FlowValidationResult {
  const issues: string[] = [];
  
  if (!isFlowObject(flow)) {
    issues.push(`${context}: Invalid flow object structure`);
    return {
      flow_id: '' as ValidatedUUID,
      validated: false,
      issues
    };
  }
  
  try {
    const flow_id = extractFlowId(flow, `${context} flow_id`);
    
    // Additional integrity checks
    if (flow.master_flow_id && flow.master_flow_id !== flow_id) {
      // Validate master flow ID if present
      try {
        validateUUID(flow.master_flow_id, `${context} master_flow_id`);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        issues.push(`Invalid master_flow_id: ${errorMessage}`);
      }
    }
    
    return {
      flow_id,
      validated: true,
      issues
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    issues.push(`Flow ID validation failed: ${errorMessage}`);
    
    return {
      flow_id: '' as ValidatedUUID,
      validated: false,
      issues
    };
  }
}

/**
 * Batch validation interfaces
 */
interface ValidFlowResult {
  flow_id: ValidatedUUID;
  original: FlowObject;
}

interface InvalidFlowResult {
  issues: string[];
  original: unknown;
}

interface FlowBatchSummary {
  total: number;
  valid: number;
  invalid: number;
  issues: string[];
}

interface FlowBatchValidationResult {
  validFlows: ValidFlowResult[];
  invalidFlows: InvalidFlowResult[];
  summary: FlowBatchSummary;
}

/**
 * Batch validation for multiple flows
 */
export function validateFlowBatch(
  flows: unknown[],
  context: string = 'Flow batch'
): FlowBatchValidationResult {
  const validFlows: ValidFlowResult[] = [];
  const invalidFlows: InvalidFlowResult[] = [];
  const allIssues: string[] = [];
  
  flows.forEach((flow, index) => {
    const validation = validateFlowObject(flow, `${context}[${index}]`);
    
    if (validation.validated && isFlowObject(flow)) {
      validFlows.push({
        flow_id: validation.flow_id,
        original: flow
      });
    } else {
      invalidFlows.push({
        issues: validation.issues,
        original: flow
      });
    }
    
    allIssues.push(...validation.issues);
  });
  
  return {
    validFlows,
    invalidFlows,
    summary: {
      total: flows.length,
      valid: validFlows.length,
      invalid: invalidFlows.length,
      issues: allIssues
    }
  };
}

/**
 * Console logging helper for UUID debugging
 */
export function debugUUID(uuid: string, context: string = 'UUID Debug'): void {
  console.group(`🔍 ${context}`);
  console.log('Value:', uuid);
  console.log('Length:', uuid.length);
  console.log('Valid:', isValidUUID(uuid));
  console.log('Characters:', uuid.split('').map((char, idx) => ({
    index: idx,
    char,
    code: char.charCodeAt(0),
    hex: char.charCodeAt(0).toString(16)
  })));
  console.groupEnd();
}