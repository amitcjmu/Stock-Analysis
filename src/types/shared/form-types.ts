/**
 * Shared Form Type Definitions
 *
 * Standardized form handling types for React Hook Form integration
 */

import type { FieldValues, Control, FieldPath } from 'react-hook-form';

/**
 * Generic form field value types
 */
export type FormFieldValue = string | number | boolean | string[] | number[] | FileList | null | undefined;

/**
 * Form field validation result
 */
export interface ValidationResult {
  /** Whether field is valid */
  valid: boolean;
  /** Validation error messages */
  errors: string[];
  /** Validation warnings (non-blocking) */
  warnings?: string[];
}

/**
 * Form field configuration
 */
export interface FormFieldConfig {
  /** Field type for rendering */
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'checkbox' | 'radio' | 'file' | 'textarea';
  /** Whether field is required */
  required?: boolean;
  /** Field placeholder text */
  placeholder?: string;
  /** Field label */
  label?: string;
  /** Field validation rules */
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: FormFieldValue) => ValidationResult;
  };
  /** Field options for select/radio fields */
  options?: Array<{
    value: string | number;
    label: string;
    disabled?: boolean;
  }>;
}

/**
 * Generic form state interface
 */
export interface FormState<TData extends FieldValues = FieldValues> {
  /** Form field values */
  values: TData;
  /** Form field errors */
  errors: Partial<Record<FieldPath<TData>, string[]>>;
  /** Form submission state */
  isSubmitting: boolean;
  /** Whether form has been touched */
  touched: Partial<Record<FieldPath<TData>, boolean>>;
  /** Whether form is valid */
  isValid: boolean;
  /** Form-level error messages */
  formErrors?: string[];
}

/**
 * Enhanced form hook configuration
 */
export interface FormHookConfig<TFieldValues extends FieldValues = FieldValues> {
  /** React Hook Form control instance */
  control: Control<TFieldValues>;
  /** Form resolver for validation */
  resolver?: (values: TFieldValues) => Promise<ValidationResult> | ValidationResult;
  /** Default form values */
  defaultValues?: Partial<TFieldValues>;
  /** Form submission handler */
  onSubmit?: (data: TFieldValues) => Promise<void> | void;
}
