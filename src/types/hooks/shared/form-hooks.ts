/**
 * Form Hook Types
 * 
 * Hook interfaces for form management including form control, field management, and validation.
 * Integrates with React Hook Form for proper TypeScript support.
 */

import type { ReactNode } from 'react';
import type { 
  FieldValues, 
  Control, 
  FieldPath, 
  FieldErrors,
  UseFormHandleSubmit,
  UseFormReset,
  UseFormSetError,
  UseFormClearErrors,
  UseFormSetValue,
  UseFormGetValues,
  UseFormTrigger,
  UseFormUnregister,
  UseFormWatch,
  UseFormRegister,
  Resolver,
  FieldError,
  RegisterOptions,
  ControllerFieldState,
  ControllerRenderProps
} from 'react-hook-form';
import type { FormHookConfig } from '../../shared/form-types';

// Form hooks
export interface UseFormParams<TFieldValues extends FieldValues = FieldValues> {
  mode?: 'onSubmit' | 'onBlur' | 'onChange' | 'onTouched' | 'all';
  reValidateMode?: 'onSubmit' | 'onBlur' | 'onChange';
  defaultValues?: Partial<TFieldValues>;
  resolver?: Resolver<TFieldValues>;
  context?: unknown;
  criteriaMode?: 'firstError' | 'all';
  shouldFocusError?: boolean;
  shouldUnregister?: boolean;
  shouldUseNativeValidation?: boolean;
  delayError?: number;
  onSubmit?: (data: TFieldValues, event?: React.BaseSyntheticEvent) => void | Promise<void>;
  onError?: (errors: FieldErrors<TFieldValues>, event?: React.BaseSyntheticEvent) => void;
  onReset?: (data?: Partial<TFieldValues>) => void;
  onInvalid?: (errors: FieldErrors<TFieldValues>, event?: React.BaseSyntheticEvent) => void;
}

export interface UseFormReturn<TFieldValues extends FieldValues = FieldValues> {
  control: Control<TFieldValues>;
  handleSubmit: UseFormHandleSubmit<TFieldValues>;
  reset: UseFormReset<TFieldValues>;
  setError: UseFormSetError<TFieldValues>;
  clearErrors: UseFormClearErrors<TFieldValues>;
  setValue: UseFormSetValue<TFieldValues>;
  getValue: (name: FieldPath<TFieldValues>) => TFieldValues[FieldPath<TFieldValues>];
  getValues: UseFormGetValues<TFieldValues>;
  trigger: UseFormTrigger<TFieldValues>;
  unregister: UseFormUnregister<TFieldValues>;
  watch: UseFormWatch<TFieldValues>;
  formState: FormState<TFieldValues>;
  register: UseFormRegister<TFieldValues>;
}

export interface FormState<TFieldValues extends FieldValues = FieldValues> {
  isDirty: boolean;
  isLoading: boolean;
  isSubmitted: boolean;
  isSubmitSuccessful: boolean;
  isSubmitting: boolean;
  isValidating: boolean;
  isValid: boolean;
  submitCount: number;
  dirtyFields: Partial<Record<FieldPath<TFieldValues>, boolean>>;
  touchedFields: Partial<Record<FieldPath<TFieldValues>, boolean>>;
  errors: FieldErrors<TFieldValues>;
  defaultValues?: Partial<TFieldValues>;
}

export interface UseFieldParams<TFieldValues extends FieldValues = FieldValues> {
  name: FieldPath<TFieldValues>;
  defaultValue?: TFieldValues[FieldPath<TFieldValues>];
  rules?: RegisterOptions<TFieldValues, FieldPath<TFieldValues>>;
  shouldUnregister?: boolean;
  disabled?: boolean;
}

export interface UseFieldReturn<TFieldValues extends FieldValues = FieldValues> {
  field: ControllerRenderProps<TFieldValues, FieldPath<TFieldValues>>;
  fieldState: ControllerFieldState;
  formState: FormState<TFieldValues>;
}