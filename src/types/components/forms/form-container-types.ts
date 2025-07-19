/**
 * Form Container Types
 * 
 * Types for form containers, form fields, and form-level configuration.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';
import { 
  BaseFormProps, 
  FormSchema, 
  FormField, 
  FormErrorInfo, 
  ScrollToFirstErrorOptions, 
  ColProps, 
  FormInstance,
  FormFieldControl
} from './base-types';

// Form container types
export interface FormProps extends BaseComponentProps {
  onSubmit?: (event: React.FormEvent<HTMLFormElement>) => void;
  onReset?: (event: React.FormEvent<HTMLFormElement>) => void;
  onInvalid?: (event: React.FormEvent<HTMLFormElement>) => void;
  autoComplete?: 'on' | 'off';
  noValidate?: boolean;
  method?: 'get' | 'post';
  action?: string;
  encType?: 'application/x-www-form-urlencoded' | 'multipart/form-data' | 'text/plain';
  target?: string;
  acceptCharset?: string;
  name?: string;
  rel?: string;
  disabled?: boolean;
  loading?: boolean;
  schema?: FormSchema;
  defaultValues?: Record<string, unknown>;
  values?: Record<string, unknown>;
  errors?: Record<string, string>;
  touched?: Record<string, boolean>;
  dirty?: boolean;
  valid?: boolean;
  submitting?: boolean;
  submitted?: boolean;
  validationMode?: 'onChange' | 'onBlur' | 'onSubmit' | 'all';
  reValidationMode?: 'onChange' | 'onBlur' | 'onSubmit';
  shouldFocusError?: boolean;
  shouldUnregister?: boolean;
  shouldUseNativeValidation?: boolean;
  criteriaMode?: 'firstError' | 'all';
  delayError?: number;
  onValuesChange?: (values: Record<string, unknown>, changedValues: Record<string, unknown>) => void;
  onFieldsChange?: (changedFields: FormField[], allFields: FormField[]) => void;
  onFinish?: (values: Record<string, unknown>) => void;
  onFinishFailed?: (errorInfo: FormErrorInfo) => void;
  validateMessages?: Record<string, string>;
  preserve?: boolean;
  requiredMark?: boolean | 'optional' | ((label: ReactNode, info: { required: boolean }) => ReactNode);
  colon?: boolean;
  scrollToFirstError?: boolean | ScrollToFirstErrorOptions;
  layout?: 'horizontal' | 'vertical' | 'inline';
  labelCol?: ColProps;
  wrapperCol?: ColProps;
  labelAlign?: 'left' | 'right';
  labelWrap?: boolean;
  size?: 'small' | 'middle' | 'large';
  component?: boolean | string | React.ComponentType<unknown>;
  fields?: FormField[];
  form?: FormInstance;
  initialValues?: Record<string, unknown>;
  validateTrigger?: string | string[];
  onReset?: () => void;
}

export interface FormFieldProps extends BaseFormProps {
  fieldKey?: string | number | (string | number)[];
  dependencies?: string[][];
  getValueFromEvent?: (...args: unknown[]) => unknown;
  getValueProps?: (value: unknown) => unknown;
  normalize?: (value: unknown, prevValue: unknown, allValues: Record<string, unknown>) => unknown;
  preserve?: boolean;
  trigger?: string;
  validateFirst?: boolean;
  validateTrigger?: string | string[];
  valuePropName?: string;
  rules?: ValidationRule[];
  shouldUpdate?: boolean | ((prevValues: unknown, curValues: unknown) => boolean);
  messageVariables?: Record<string, string>;
  initialValue?: unknown;
  tooltip?: ReactNode;
  extra?: ReactNode;
  hasFeedback?: boolean;
  validateStatus?: 'success' | 'warning' | 'error' | 'validating' | '';
  noStyle?: boolean;
  hidden?: boolean;
  wrapperCol?: ColProps;
  labelCol?: ColProps;
  colon?: boolean;
  labelAlign?: 'left' | 'right';
  htmlFor?: string;
  children?: ReactNode | ((control: FormFieldControl, meta: FormFieldMeta, form: FormInstance) => ReactNode);
}

// Supporting types
export interface FormFieldMeta {
  touched?: boolean;
  validating?: boolean;
  errors?: string[];
  warnings?: string[];
  name: string | string[];
}

export interface ValidationRule {
  // Add validation rule properties as needed
}