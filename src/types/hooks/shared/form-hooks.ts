/**
 * Form Hook Types
 * 
 * Hook interfaces for form management including form control, field management, and validation.
 */

import { ReactNode } from 'react';

// Form hooks
export interface UseFormParams<TFieldValues = any> {
  mode?: 'onSubmit' | 'onBlur' | 'onChange' | 'onTouched' | 'all';
  reValidateMode?: 'onSubmit' | 'onBlur' | 'onChange';
  defaultValues?: Partial<TFieldValues>;
  resolver?: unknown;
  context?: unknown;
  criteriaMode?: 'firstError' | 'all';
  shouldFocusError?: boolean;
  shouldUnregister?: boolean;
  shouldUseNativeValidation?: boolean;
  delayError?: number;
  onSubmit?: (data: TFieldValues, event?: unknown) => void | Promise<void>;
  onError?: (errors: any, event?: unknown) => void;
  onReset?: (data?: TFieldValues) => void;
  onInvalid?: (errors: any, event?: unknown) => void;
}

export interface UseFormReturn<TFieldValues = any> {
  control: unknown;
  handleSubmit: (onValid: (data: TFieldValues, event?: unknown) => void | Promise<void>, onInvalid?: (errors: any, event?: unknown) => void) => (event?: unknown) => Promise<void>;
  reset: (values?: Partial<TFieldValues>, options?: unknown) => void;
  setError: (name: string, error: any, options?: unknown) => void;
  clearErrors: (name?: string | string[]) => void;
  setValue: (name: string, value: any, options?: unknown) => void;
  getValue: (name: string) => any;
  getValues: (names?: string | string[]) => any;
  trigger: (name?: string | string[]) => Promise<boolean>;
  unregister: (name?: string | string[], options?: unknown) => void;
  watch: (name?: string | string[] | ((data: any, options: unknown) => any), defaultValue?: unknown) => any;
  formState: FormState<TFieldValues>;
  register: (name: string, options?: unknown) => any;
}

export interface FormState<TFieldValues = any> {
  isDirty: boolean;
  isLoading: boolean;
  isSubmitted: boolean;
  isSubmitSuccessful: boolean;
  isSubmitting: boolean;
  isValidating: boolean;
  isValid: boolean;
  submitCount: number;
  dirtyFields: Partial<Record<string, boolean>>;
  touchedFields: Partial<Record<string, boolean>>;
  errors: unknown;
  defaultValues?: Partial<TFieldValues>;
}

export interface UseFieldParams {
  name: string;
  defaultValue?: unknown;
  rules?: unknown;
  shouldUnregister?: boolean;
  disabled?: boolean;
}

export interface UseFieldReturn {
  field: {
    name: string;
    value: unknown;
    onChange: (value: unknown) => void;
    onBlur: () => void;
    ref: unknown;
  };
  fieldState: {
    invalid: boolean;
    isTouched: boolean;
    isDirty: boolean;
    error?: unknown;
  };
  formState: FormState;
}