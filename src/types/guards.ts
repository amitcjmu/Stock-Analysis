/**
 * Type Guards and Validation Utilities
 *
 * Provides runtime type checking and validation utilities that complement
 * the TypeScript compile-time type checking system.
 */

// Flow Type Guards
export const isDiscoveryFlow = (obj: unknown): obj is import('./modules/discovery').DiscoveryFlow.Models.FlowData => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.flow_name === 'string' &&
    typeof obj.status === 'string' &&
    Array.isArray(obj.phases);
};

export const isFlowState = (obj: unknown): obj is import('./modules/flow-orchestration').FlowOrchestration.Models.FlowState => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.flow_id === 'string' &&
    typeof obj.status === 'string' &&
    typeof obj.current_phase === 'string' &&
    typeof obj.progress === 'number';
};

export const isAgentConfiguration = (obj: unknown): obj is import('./modules/flow-orchestration').FlowOrchestration.Models.AgentConfiguration => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.name === 'string' &&
    typeof obj.type === 'string' &&
    typeof obj.enabled === 'boolean';
};

// Component Type Guards
// Legacy NavigationSidebar type guard removed

export const isFieldMappingProps = (obj: unknown): obj is import('./components/discovery').FieldMappingsTabProps => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.flow_id === 'string' &&
    Array.isArray(obj.mappings);
};

export const isFormProps = (obj: unknown): obj is import('./components/forms').FormProps => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.onSubmit === 'function';
};

// Hook Type Guards
export const isAttributeMappingReturn = (obj: unknown): obj is import('./hooks/discovery').UseAttributeMappingReturn => {
  return obj &&
    typeof obj === 'object' &&
    Array.isArray(obj.mappings) &&
    Array.isArray(obj.critical_attributes) &&
    typeof obj.flow_id === 'string';
};

export const isAsyncHookReturn = (obj: unknown): obj is import('./hooks/shared').BaseAsyncHookReturn => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.isLoading === 'boolean' &&
    typeof obj.isError === 'boolean' &&
    typeof obj.isSuccess === 'boolean' &&
    typeof obj.refetch === 'function';
};

// API Type Guards
export const isBaseApiRequest = (obj: unknown): obj is import('./api/shared').BaseApiRequest => {
  return obj &&
    typeof obj === 'object' &&
    (obj.requestId === undefined || typeof obj.requestId === 'string') &&
    (obj.timestamp === undefined || typeof obj.timestamp === 'string');
};

export const isBaseApiResponse = (obj: unknown): obj is import('./api/shared').BaseApiResponse => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.success === 'boolean' &&
    typeof obj.metadata === 'object';
};

export const isMultiTenantContext = (obj: unknown): obj is import('./api/shared').MultiTenantContext => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.client_account_id === 'string' &&
    typeof obj.engagement_id === 'string' &&
    typeof obj.user_id === 'string';
};

// Utility Type Guards
export const isValidationResult = (obj: unknown): obj is import('./api/shared').ValidationResult => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.is_valid === 'boolean' &&
    Array.isArray(obj.errors) &&
    Array.isArray(obj.warnings);
};

export const isPaginationInfo = (obj: unknown): obj is import('./api/shared').PaginationInfo => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.page === 'number' &&
    typeof obj.page_size === 'number' &&
    typeof obj.total === 'number' &&
    typeof obj.has_next === 'boolean' &&
    typeof obj.has_previous === 'boolean';
};

// Complex Type Guards
export const isDiscoveryFlowRequest = (obj: unknown): obj is import('./api/discovery').InitializeDiscoveryFlowRequest => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.flow_name === 'string' &&
    isMultiTenantContext(obj.context);
};

export const isFieldMapping = (obj: unknown): obj is import('./hooks/discovery').FieldMapping => {
  return obj &&
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.source_field === 'string' &&
    typeof obj.target_field === 'string' &&
    typeof obj.mapping_type === 'string' &&
    typeof obj.confidence === 'number';
};

// Array Type Guards
export const isFieldMappingArray = (obj: unknown): obj is Array<import('./hooks/discovery').FieldMapping> => {
  return Array.isArray(obj) && obj.every(isFieldMapping);
};

export const isValidationResultArray = (obj: unknown): obj is Array<import('./api/shared').ValidationResult> => {
  return Array.isArray(obj) && obj.every(isValidationResult);
};

// Generic Type Guard Creator
export const createTypeGuard = <T>(
  validator: (obj: unknown) => boolean,
  typeName: string
): (obj: unknown) => obj is T => {
  const guard = (obj: unknown): obj is T => {
    const isValid = validator(obj);
    if (!isValid && process.env.NODE_ENV === 'development') {
      console.warn(`Type guard failed for ${typeName}:`, obj);
    }
    return isValid;
  };

  // Add metadata for debugging
  Object.defineProperty(guard, 'typeName', {
    value: typeName,
    writable: false,
    enumerable: true
  });

  return guard;
};

// Enhanced Type Guards with Error Reporting
export const createValidatingTypeGuard = <T>(
  validator: (obj: unknown) => { isValid: boolean; errors: string[] },
  typeName: string
): { guard: (obj: unknown) => obj is T; validator: (obj: unknown) => { isValid: boolean; errors: string[] } } => {
  return {
    guard: (obj: unknown): obj is T => {
      const result = validator(obj);
      if (!result.isValid && process.env.NODE_ENV === 'development') {
        console.warn(`Type validation failed for ${typeName}:`, {
          object: obj,
          errors: result.errors
        });
      }
      return result.isValid;
    },
    validate: (obj: unknown) => validator(obj),
    typeName
  };
};

// Schema-based Validation
export interface ValidationSchema {
  [key: string]: {
    type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'function';
    required?: boolean;
    nullable?: boolean;
    validator?: (value: unknown) => boolean;
    arrayItemValidator?: (item: unknown) => boolean;
    properties?: ValidationSchema;
  };
}

export const validateSchema = (obj: unknown, schema: ValidationSchema): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];

  for (const [key, config] of Object.entries(schema)) {
    const value = obj?.[key];

    // Check required fields
    if (config.required && (value === undefined || value === null)) {
      errors.push(`Required field '${key}' is missing`);
      continue;
    }

    // Skip validation for non-required, undefined/null values
    if (!config.required && (value === undefined || (value === null && !config.nullable))) {
      continue;
    }

    // Type checking
    const actualType = Array.isArray(value) ? 'array' : typeof value;
    if (actualType !== config.type) {
      errors.push(`Field '${key}' expected type '${config.type}' but got '${actualType}'`);
      continue;
    }

    // Custom validation
    if (config.validator && !config.validator(value)) {
      errors.push(`Field '${key}' failed custom validation`);
    }

    // Array item validation
    if (config.type === 'array' && config.arrayItemValidator && Array.isArray(value)) {
      value.forEach((item, index) => {
        if (!config.arrayItemValidator(item)) {
          errors.push(`Array item at index ${index} in field '${key}' failed validation`);
        }
      });
    }

    // Nested object validation
    if (config.type === 'object' && config.properties && value) {
      const nestedResult = validateSchema(value, config.properties);
      if (!nestedResult.isValid) {
        errors.push(...nestedResult.errors.map(error => `${key}.${error}`));
      }
    }
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

// Common Schemas
export const COMMON_SCHEMAS: Record<string, ValidationSchema> = {
  BaseApiRequest: {
    requestId: { type: 'string', required: false },
    timestamp: { type: 'string', required: false },
    version: { type: 'string', required: false },
    metadata: { type: 'object', required: false }
  },

  BaseApiResponse: {
    success: { type: 'boolean', required: true },
    data: { type: 'object', required: false },
    message: { type: 'string', required: false },
    error: { type: 'object', required: false },
    metadata: { type: 'object', required: true }
  },

  MultiTenantContext: {
    client_account_id: { type: 'string', required: true },
    engagement_id: { type: 'string', required: true },
    user_id: { type: 'string', required: true },
    tenant_id: { type: 'string', required: false },
    organization_id: { type: 'string', required: false }
  },

  FieldMapping: {
    id: { type: 'string', required: true },
    source_field: { type: 'string', required: true },
    target_field: { type: 'string', required: true },
    mapping_type: { type: 'string', required: true },
    confidence: { type: 'number', required: true, validator: (v) => v >= 0 && v <= 1 },
    status: { type: 'string', required: true },
    created_at: { type: 'string', required: true },
    updated_at: { type: 'string', required: true }
  }
};

// Schema-based Type Guards
export const createSchemaTypeGuard = <T>(schemaName: string): { guard: (obj: unknown) => obj is T; validator: (obj: unknown) => { isValid: boolean; errors: string[] } } => {
  const schema = COMMON_SCHEMAS[schemaName];
  if (!schema) {
    throw new Error(`Schema '${schemaName}' not found`);
  }

  return createValidatingTypeGuard<T>(
    (obj) => validateSchema(obj, schema),
    schemaName
  );
};

// Pre-configured Schema Guards
export const BaseApiRequestGuard = createSchemaTypeGuard<import('./api/shared').BaseApiRequest>('BaseApiRequest');
export const BaseApiResponseGuard = createSchemaTypeGuard<import('./api/shared').BaseApiResponse>('BaseApiResponse');
export const MultiTenantContextGuard = createSchemaTypeGuard<import('./api/shared').MultiTenantContext>('MultiTenantContext');
export const FieldMappingGuard = createSchemaTypeGuard<import('./hooks/discovery').FieldMapping>('FieldMapping');

// Runtime Type Registry
export class TypeRegistry {
  private static guards = new Map<string, (obj: unknown) => boolean>();
  private static schemas = new Map<string, ValidationSchema>();

  static register<T>(typeName: string, guard: (obj: unknown) => obj is T): void {
    this.guards.set(typeName, guard);
  }

  static registerSchema(typeName: string, schema: ValidationSchema): void {
    this.schemas.set(typeName, schema);
    this.guards.set(typeName, (obj) => validateSchema(obj, schema).isValid);
  }

  static check<T>(typeName: string, obj: unknown): obj is T {
    const guard = this.guards.get(typeName);
    if (!guard) {
      throw new Error(`Type guard for '${typeName}' not registered`);
    }
    return guard(obj);
  }

  static validate(typeName: string, obj: unknown): { isValid: boolean; errors: string[] } {
    const schema = this.schemas.get(typeName);
    if (!schema) {
      // Fallback to simple guard check
      const guard = this.guards.get(typeName);
      if (!guard) {
        throw new Error(`No validator for type '${typeName}'`);
      }
      return { isValid: guard(obj), errors: [] };
    }
    return validateSchema(obj, schema);
  }

  static getRegisteredTypes(): string[] {
    return Array.from(this.guards.keys());
  }
}

// Auto-register common type guards
TypeRegistry.register('DiscoveryFlow', isDiscoveryFlow);
TypeRegistry.register('FlowState', isFlowState);
TypeRegistry.register('AgentConfiguration', isAgentConfiguration);
TypeRegistry.register('BaseApiRequest', isBaseApiRequest);
TypeRegistry.register('BaseApiResponse', isBaseApiResponse);
TypeRegistry.register('MultiTenantContext', isMultiTenantContext);
TypeRegistry.register('FieldMapping', isFieldMapping);

// Register schemas
Object.entries(COMMON_SCHEMAS).forEach(([name, schema]) => {
  TypeRegistry.registerSchema(name, schema);
});

// Development Utilities
export const DEV_TYPE_GUARDS = {
  listRegisteredTypes: () => TypeRegistry.getRegisteredTypes(),
  validateType: (typeName: string, obj: unknown) => TypeRegistry.validate(typeName, obj),
  checkType: (typeName: string, obj: unknown) => TypeRegistry.check(typeName, obj),
  createTestGuard: <T>(validator: (obj: unknown) => boolean) =>
    createTypeGuard<T>(validator, 'TestType')
} as const;
