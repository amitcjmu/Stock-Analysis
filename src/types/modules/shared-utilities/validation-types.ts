/**
 * Validation Utilities Types
 * 
 * Types for data validation, sanitization, and form validation.
 */

// Validation service interfaces
export interface ValidationService {
  validate: (data: unknown, schema: ValidationSchema) => ValidationResult;
  validateAsync: (data: unknown, schema: ValidationSchema) => Promise<ValidationResult>;
  createSchema: (definition: SchemaDefinition) => ValidationSchema;
  addRule: (name: string, rule: ValidationRule) => void;
  removeRule: (name: string) => void;
  getRule: (name: string) => ValidationRule | undefined;
}

export interface SanitizationService {
  sanitize: (data: unknown, rules: SanitizationRules) => unknown;
  sanitizeHtml: (html: string, options?: HtmlSanitizationOptions) => string;
  sanitizeInput: (input: string, type: InputType) => string;
  preventXSS: (input: string) => string;
  preventSQLInjection: (input: string) => string;
}

export interface FormValidationService {
  validateForm: (formData: FormData, schema: FormSchema) => FormValidationResult;
  validateField: (fieldName: string, value: unknown, rules: FieldRules) => FieldValidationResult;
  createFormSchema: (fields: FieldDefinition[]) => FormSchema;
  addFieldRule: (fieldName: string, rule: FieldRule) => void;
  removeFieldRule: (fieldName: string, ruleName: string) => void;
}

// Validation model types
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  data?: unknown;
  metadata?: Record<string, unknown>;
}

export interface ValidationSchema {
  type: 'object' | 'array' | 'string' | 'number' | 'boolean' | 'date';
  properties?: Record<string, ValidationSchema>;
  items?: ValidationSchema;
  rules: ValidationRule[];
  required?: string[];
  optional?: string[];
}

export interface ValidationRule {
  name: string;
  validate: (value: unknown, context?: ValidationContext) => boolean | Promise<boolean>;
  message: string;
  parameters?: Record<string, unknown>;
  severity: 'error' | 'warning' | 'info';
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value: unknown;
  severity: 'error' | 'warning' | 'info';
  metadata?: Record<string, unknown>;
}

export interface ValidationWarning {
  field: string;
  message: string;
  code: string;
  value: unknown;
  suggestion?: string;
  metadata?: Record<string, unknown>;
}

export interface ValidationContext {
  parentValue?: unknown;
  rootValue?: unknown;
  path: string[];
  metadata?: Record<string, unknown>;
}

export interface SchemaDefinition {
  type: string;
  properties?: Record<string, SchemaDefinition>;
  items?: SchemaDefinition;
  rules?: string[];
  required?: string[];
  optional?: string[];
  metadata?: Record<string, unknown>;
}

export interface SanitizationRules {
  [field: string]: SanitizationRule[];
}

export interface SanitizationRule {
  type: 'trim' | 'lowercase' | 'uppercase' | 'escape' | 'strip' | 'replace' | 'custom';
  parameters?: Record<string, unknown>;
  apply: (value: unknown, parameters?: Record<string, unknown>) => unknown;
}

export interface HtmlSanitizationOptions {
  allowedTags: string[];
  allowedAttributes: Record<string, string[]>;
  allowedSchemes: string[];
  stripTags: boolean;
  stripAttributes: boolean;
}

export interface FormData {
  [field: string]: unknown;
}

export interface FormSchema {
  fields: Record<string, FieldSchema>;
  rules: FormRule[];
  metadata?: Record<string, unknown>;
}

export interface FieldSchema {
  type: string;
  rules: FieldRule[];
  required: boolean;
  label: string;
  placeholder?: string;
  defaultValue?: unknown;
  metadata?: Record<string, unknown>;
}

export interface FormValidationResult {
  isValid: boolean;
  errors: Record<string, FieldValidationResult>;
  warnings: Record<string, FieldValidationResult>;
  data: FormData;
  metadata?: Record<string, unknown>;
}

export interface FieldValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  value: unknown;
}

export interface FieldDefinition {
  name: string;
  type: string;
  label: string;
  required: boolean;
  rules: FieldRule[];
  placeholder?: string;
  defaultValue?: unknown;
  metadata?: Record<string, unknown>;
}

export interface FieldRules {
  [ruleName: string]: FieldRule;
}

export interface FieldRule {
  name: string;
  validate: (value: unknown, context?: FieldValidationContext) => boolean | Promise<boolean>;
  message: string;
  parameters?: Record<string, unknown>;
  severity: 'error' | 'warning' | 'info';
}

export interface FormRule {
  name: string;
  validate: (formData: FormData, context?: FormValidationContext) => boolean | Promise<boolean>;
  message: string;
  parameters?: Record<string, unknown>;
  severity: 'error' | 'warning' | 'info';
}

export interface FieldValidationContext {
  fieldName: string;
  formData: FormData;
  metadata?: Record<string, unknown>;
}

export interface FormValidationContext {
  formData: FormData;
  metadata?: Record<string, unknown>;
}

export type InputType = 'text' | 'email' | 'url' | 'number' | 'phone' | 'html' | 'json' | 'sql';