/**
 * Validation Types
 *
 * Common validation interfaces used across CRUD operations and import/export.
 */

import type { PrimitiveValue, DynamicValue, ConditionValue } from './value-types';

export interface ValidationError {
  field: string;
  code: string;
  message: string;
  value?: DynamicValue;
  constraint?: ConditionValue;
}

export interface ValidationWarning {
  field: string;
  code: string;
  message: string;
  value?: DynamicValue;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  summary?: {
    totalErrors: number;
    totalWarnings: number;
    errorsByField: Record<string, number>;
    warningsByField: Record<string, number>;
  };
}

export interface ValidationOptions {
  strict?: boolean;
  skipFields?: string[];
  customRules?: ValidationRule[];
  warningsAsErrors?: boolean;
}

export interface ValidationRuleParams {
  [key: string]: string | number | boolean | string[] | number[];
}

export interface ValidationRule {
  field: string;
  validator: string;
  params?: ValidationRuleParams;
  message?: string;
}
