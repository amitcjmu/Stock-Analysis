/**
 * Form Types
 * 
 * Form field definitions, validation rules, and form-related
 * configuration types.
 */

export interface FormField {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  placeholder?: string;
  helpText?: string;
  validation?: ValidationRule[];
  options?: FieldOption[];
  dependencies?: FieldDependency[];
  conditional?: FieldConditional[];
  metadata?: Record<string, string | number | boolean | null>;
}

export interface ValidationRule {
  type: ValidationType;
  value?: unknown;
  message: string;
  validator?: (value: unknown) => boolean | Promise<boolean>;
}

export interface FieldOption {
  label: string;
  value: unknown;
  disabled?: boolean;
  description?: string;
  group?: string;
  icon?: string;
}

export interface FieldDependency {
  field: string;
  value: unknown;
  operation: DependencyOperation;
}

export interface FieldConditional {
  condition: ConditionalExpression;
  action: ConditionalAction;
  target?: string;
}

export interface ConditionalExpression {
  field: string;
  operator: ConditionalOperator;
  value: unknown;
  logic?: 'and' | 'or';
  nested?: ConditionalExpression[];
}

export interface ConditionalAction {
  type: 'show' | 'hide' | 'enable' | 'disable' | 'require' | 'setValue';
  value?: unknown;
}

// Enum and union types
export type FieldType = 'text' | 'textarea' | 'email' | 'url' | 'password' | 'number' | 'phone' | 'date' | 'datetime' | 'time' | 'select' | 'multiselect' | 'checkbox' | 'radio' | 'switch' | 'slider' | 'file' | 'image' | 'color' | 'json' | 'custom';
export type ValidationType = 'required' | 'email' | 'url' | 'phone' | 'min' | 'max' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
export type DependencyOperation = 'equals' | 'not_equals' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'contains' | 'not_contains';
export type ConditionalOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in' | 'is_empty' | 'is_not_empty';