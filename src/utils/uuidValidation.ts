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
 * Safely extracts flow ID from various possible sources with validation
 */
export function extractFlowId(
  source: { flow_id?: string; flowId?: string; id?: string } | string,
  context: string = 'Flow ID'
): ValidatedUUID {
  let flowId: string;
  
  if (typeof source === 'string') {
    flowId = source;
  } else {
    // Try different possible field names
    flowId = source.flow_id || source.flowId || source.id || '';
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
 * Deep validation for flow objects to ensure ID integrity
 */
export function validateFlowObject(flow: any, context: string = 'Flow object'): {
  flow_id: ValidatedUUID;
  validated: boolean;
  issues: string[];
} {
  const issues: string[] = [];
  
  try {
    const flow_id = extractFlowId(flow, `${context} flow_id`);
    
    // Additional integrity checks
    if (flow.master_flow_id && flow.master_flow_id !== flow_id) {
      // Validate master flow ID if present
      try {
        validateUUID(flow.master_flow_id, `${context} master_flow_id`);
      } catch (error) {
        issues.push(`Invalid master_flow_id: ${error.message}`);
      }
    }
    
    return {
      flow_id,
      validated: true,
      issues
    };
  } catch (error) {
    issues.push(`Flow ID validation failed: ${error.message}`);
    
    return {
      flow_id: '' as ValidatedUUID,
      validated: false,
      issues
    };
  }
}

/**
 * Batch validation for multiple flows
 */
export function validateFlowBatch(flows: any[], context: string = 'Flow batch'): {
  validFlows: Array<{ flow_id: ValidatedUUID; original: any }>;
  invalidFlows: Array<{ issues: string[]; original: any }>;
  summary: {
    total: number;
    valid: number;
    invalid: number;
    issues: string[];
  };
} {
  const validFlows: Array<{ flow_id: ValidatedUUID; original: any }> = [];
  const invalidFlows: Array<{ issues: string[]; original: any }> = [];
  const allIssues: string[] = [];
  
  flows.forEach((flow, index) => {
    const validation = validateFlowObject(flow, `${context}[${index}]`);
    
    if (validation.validated) {
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