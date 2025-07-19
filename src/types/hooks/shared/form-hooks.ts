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
  resolver?: any;
  context?: any;
  criteriaMode?: 'firstError' | 'all';
  shouldFocusError?: boolean;
  shouldUnregister?: boolean;
  shouldUseNativeValidation?: boolean;
  delayError?: number;
  onSubmit?: (data: TFieldValues, event?: any) => void | Promise<void>;
  onError?: (errors: any, event?: any) => void;
  onReset?: (data?: TFieldValues) => void;
  onInvalid?: (errors: any, event?: any) => void;
}

export interface UseFormReturn<TFieldValues = any> {
  control: any;
  handleSubmit: (onValid: (data: TFieldValues, event?: any) => void | Promise<void>, onInvalid?: (errors: any, event?: any) => void) => (event?: any) => Promise<void>;
  reset: (values?: Partial<TFieldValues>, options?: any) => void;
  setError: (name: string, error: any, options?: any) => void;
  clearErrors: (name?: string | string[]) => void;
  setValue: (name: string, value: any, options?: any) => void;
  getValue: (name: string) => any;
  getValues: (names?: string | string[]) => any;
  trigger: (name?: string | string[]) => Promise<boolean>;
  unregister: (name?: string | string[], options?: any) => void;
  watch: (name?: string | string[] | ((data: any, options: any) => any), defaultValue?: any) => any;
  formState: FormState<TFieldValues>;
  register: (name: string, options?: any) => any;
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
  errors: any;
  defaultValues?: Partial<TFieldValues>;
}

export interface UseFieldParams {
  name: string;
  defaultValue?: any;
  rules?: any;
  shouldUnregister?: boolean;
  disabled?: boolean;
}

export interface UseFieldReturn {
  field: {
    name: string;
    value: any;
    onChange: (value: any) => void;
    onBlur: () => void;
    ref: any;
  };
  fieldState: {
    invalid: boolean;
    isTouched: boolean;
    isDirty: boolean;
    error?: any;
  };
  formState: FormState;
}