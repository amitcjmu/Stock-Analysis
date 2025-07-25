/**
 * Shared Configuration Type Definitions
 *
 * Standardized configuration value types to replace any types in constraint
 * and criteria systems
 */

/**
 * Union type for common configuration values across the platform
 */
export type ConfigurationValue =
  | string
  | number
  | boolean
  | string[]
  | number[]
  | ConfigurationObject;

/**
 * Complex configuration object structure
 */
export interface ConfigurationObject {
  [key: string]: ConfigurationValue | undefined;
}

/**
 * Typed constraint interface for validation and business rules
 */
export interface TypedConstraint {
  /** Constraint type identifier */
  type: string;
  /** Constraint value */
  value: ConfigurationValue;
  /** Human-readable description */
  description: string;
  /** Impact level of constraint violation */
  impact: 'low' | 'medium' | 'high' | 'critical';
  /** Whether constraint is actively enforced */
  enabled?: boolean;
  /** Constraint validation metadata */
  validation?: {
    required: boolean;
    min?: number;
    max?: number;
    pattern?: string;
    allowedValues?: unknown[];
  };
}

/**
 * Configuration criteria for decision-making systems
 */
export interface ConfigurationCriteria {
  /** Criteria identifier */
  id: string;
  /** Criteria name */
  name: string;
  /** Criteria value */
  value: ConfigurationValue;
  /** Weight for multi-criteria decisions */
  weight?: number;
  /** Criteria evaluation operator */
  operator?: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'like';
  /** Reference values for comparison */
  referenceValue?: ConfigurationValue;
}
