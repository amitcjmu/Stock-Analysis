/**
 * Value Types
 *
 * Common value types used across API types for fields with dynamic values.
 */

// Primitive value types
export type PrimitiveValue = string | number | boolean | null;

// Extended value types including arrays and dates
export type ExtendedValue = PrimitiveValue | Date | string[] | number[];

// Condition value type for filters and rules
export type ConditionValue = string | number | boolean | string[] | number[] | {
  min?: number;
  max?: number;
  contains?: string;
  startsWith?: string;
  endsWith?: string;
  regex?: string;
  in?: Array<string | number>;
  notIn?: Array<string | number>;
};

// Metric value type
export type MetricValue = number | {
  value: number;
  unit?: string;
  timestamp?: string;
  tags?: Record<string, string>;
};

// Threshold value type
export type ThresholdValue = number | {
  warning?: number;
  critical?: number;
  unit?: string;
  comparison?: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq';
};

// Configuration value type
export type ConfigValue = string | number | boolean | string[] | {
  value: string | number | boolean;
  encrypted?: boolean;
  source?: 'default' | 'environment' | 'file' | 'database';
  override?: boolean;
};

// Parameter value type
export type ParameterValue = string | number | boolean | string[] | number[] | {
  type: 'string' | 'number' | 'boolean' | 'array' | 'object';
  value: PrimitiveValue | PrimitiveValue[];
  required?: boolean;
  default?: PrimitiveValue;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    enum?: Array<string | number>;
  };
};

// Filter value type
export type FilterValue = PrimitiveValue | PrimitiveValue[] | {
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin' | 'contains' | 'startsWith' | 'endsWith' | 'regex';
  value: PrimitiveValue | PrimitiveValue[];
  caseSensitive?: boolean;
};

// Rollover condition value
export type RolloverValue = number | string | {
  size?: string;  // e.g., "50GB", "100MB"
  age?: string;   // e.g., "7d", "30d", "1h"
  docs?: number;  // number of documents
  custom?: Record<string, string | number>;
};

// Credential value type
export type CredentialValue = string | {
  type: 'password' | 'token' | 'certificate' | 'key';
  value: string;
  encrypted: boolean;
  expiresAt?: string;
};

// Dynamic field value
export type DynamicValue = PrimitiveValue | ExtendedValue | Record<string, PrimitiveValue> | Array<PrimitiveValue | Record<string, PrimitiveValue>>;
