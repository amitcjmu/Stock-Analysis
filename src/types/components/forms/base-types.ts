/**
 * Base Form Types
 * 
 * Common base interfaces and utilities used across all form components.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../shared';

// Form field control interface
export interface FormFieldControl {
  value: unknown;
  onChange: (value: unknown) => void;
  onBlur: () => void;
  onFocus: () => void;
  name: string;
  [key: string]: unknown;
}

// Validation interfaces
export interface ValidationOptions {
  first?: boolean;
  messages?: Record<string, string>;
  [key: string]: unknown;
}

export interface ValidationCallback {
  (error?: string | Error): void;
}

// Form action and entity types
export interface FormAction {
  type: string;
  payload?: unknown;
}

export interface FormFieldEntity {
  name: string | string[];
  validateTrigger?: string | string[];
  rules?: ValidationRule[];
  dependencies?: string[][];
  initialValue?: unknown;
}

export interface FormErrorField {
  name: string | string[];
  errors: string[];
  warnings?: string[];
}

// Base form props
export interface BaseFormProps extends BaseComponentProps {
  name?: string;
  form?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  error?: string | null;
  warning?: string | null;
  success?: boolean;
  hint?: string;
  label?: ReactNode;
  labelPosition?: 'top' | 'left' | 'right' | 'bottom';
  labelWidth?: number | string;
  labelAlign?: 'left' | 'center' | 'right';
  hideLabel?: boolean;
  description?: ReactNode;
  validationTrigger?: 'onChange' | 'onBlur' | 'onSubmit' | 'manual';
  validateOnMount?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined' | 'borderless' | 'flushed';
  fullWidth?: boolean;
}

// Form internal hooks
export interface FormInternalHooks {
  dispatch: (action: FormAction) => void;
  registerField: (entity: FormFieldEntity) => () => void;
  useSubscribe: (subscribable: boolean) => void;
  setInitialValues: (values: Record<string, unknown>, init: boolean) => void;
  setCallbacks: (callbacks: Record<string, unknown>) => void;
  getFields: () => FormFieldEntity[];
  setValidateMessages: (messages: Record<string, string>) => void;
  setPreserve: (preserve: boolean) => void;
  getInitialValue: (name: string | string[]) => unknown;
}

// Placeholder types that need to be defined based on actual implementation
export interface ValidationRule {
  // Add validation rule properties as needed
}

export interface FormSchema {
  // Add form schema properties as needed
}

export interface FormField {
  // Add form field properties as needed
}

export interface FormErrorInfo {
  // Add form error info properties as needed
}

export interface ScrollToFirstErrorOptions {
  // Add scroll options as needed
}

export interface ColProps {
  // Add column props as needed
}

export interface FormInstance {
  // Add form instance properties as needed
}