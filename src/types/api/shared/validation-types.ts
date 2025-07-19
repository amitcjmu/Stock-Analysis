/**
 * Validation Types
 * 
 * Common validation interfaces used across CRUD operations and import/export.
 */

export interface ValidationError {
  field: string;
  code: string;
  message: string;
  value?: any;
  constraint?: any;
}

export interface ValidationWarning {
  field: string;
  code: string;
  message: string;
  value?: any;
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

export interface ValidationRule {
  field: string;
  validator: string;
  params?: Record<string, any>;
  message?: string;
}