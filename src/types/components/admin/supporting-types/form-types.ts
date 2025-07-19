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
  metadata?: Record<string, any>;
}

export interface ValidationRule {
  type: ValidationType;
  value?: any;
  message: string;
  validator?: (value: any) => boolean | Promise<boolean>;
}

export interface FieldOption {
  label: string;
  value: any;
  disabled?: boolean;
  description?: string;
  group?: string;
  icon?: string;
}

export interface FieldDependency {
  field: string;
  value: any;
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
  value: any;
  logic?: 'and' | 'or';
  nested?: ConditionalExpression[];
}

export interface ConditionalAction {
  type: 'show' | 'hide' | 'enable' | 'disable' | 'require' | 'setValue';
  value?: any;
}

// Enum and union types
export type FieldType = 'text' | 'textarea' | 'email' | 'url' | 'password' | 'number' | 'phone' | 'date' | 'datetime' | 'time' | 'select' | 'multiselect' | 'checkbox' | 'radio' | 'switch' | 'slider' | 'file' | 'image' | 'color' | 'json' | 'custom';
export type ValidationType = 'required' | 'email' | 'url' | 'phone' | 'min' | 'max' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
export type DependencyOperation = 'equals' | 'not_equals' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'contains' | 'not_contains';
export type ConditionalOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in' | 'is_empty' | 'is_not_empty';