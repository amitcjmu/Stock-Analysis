/**
 * Choice Component Types
 * 
 * Types for checkbox, radio, switch, and other choice-based form components.
 */

import { ReactNode, RefObject } from 'react';
import { BaseFormProps } from './base-types';

// Checkbox component types
export interface CheckboxProps extends BaseFormProps {
  checked?: boolean;
  defaultChecked?: boolean;
  indeterminate?: boolean;
  value?: unknown;
  onChange?: (checked: boolean, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  children?: ReactNode;
  checkIcon?: ReactNode;
  indeterminateIcon?: ReactNode;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  rounded?: boolean;
  animation?: boolean;
  ripple?: boolean;
  autoFocus?: boolean;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLLabelElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  checkboxClassName?: string;
  labelClassName?: string;
  iconClassName?: string;
}

export interface CheckboxGroupProps extends BaseFormProps {
  value?: unknown[];
  defaultValue?: unknown[];
  options?: CheckboxOption[];
  children?: ReactNode;
  onChange?: (value: unknown[], event?: React.ChangeEvent<HTMLInputElement>) => void;
  direction?: 'horizontal' | 'vertical';
  spacing?: number | string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  color?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  checkAllEnabled?: boolean;
  checkAllText?: string;
  onCheckAll?: (checked: boolean) => void;
  groupRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  groupClassName?: string;
  itemClassName?: string;
}

// Radio component types
export interface RadioProps extends BaseFormProps {
  checked?: boolean;
  defaultChecked?: boolean;
  value?: unknown;
  onChange?: (value: unknown, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  children?: ReactNode;
  radioIcon?: ReactNode;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  animation?: boolean;
  ripple?: boolean;
  autoFocus?: boolean;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLLabelElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  radioClassName?: string;
  labelClassName?: string;
  iconClassName?: string;
}

export interface RadioGroupProps extends BaseFormProps {
  value?: unknown;
  defaultValue?: unknown;
  options?: RadioOption[];
  children?: ReactNode;
  onChange?: (value: unknown, event: React.ChangeEvent<HTMLInputElement>) => void;
  direction?: 'horizontal' | 'vertical';
  spacing?: number | string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  color?: string;
  disabled?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  groupRef?: RefObject<HTMLDivElement>;
  wrapperClassName?: string;
  groupClassName?: string;
  itemClassName?: string;
}

// Switch component types
export interface SwitchProps extends BaseFormProps {
  checked?: boolean;
  defaultChecked?: boolean;
  value?: unknown;
  onChange?: (checked: boolean, event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  onFocus?: (event: React.FocusEvent<HTMLInputElement>) => void;
  children?: ReactNode;
  onLabel?: ReactNode;
  offLabel?: ReactNode;
  checkedIcon?: ReactNode;
  uncheckedIcon?: ReactNode;
  color?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'filled' | 'outlined';
  thumbColor?: string;
  trackColor?: string;
  animation?: boolean;
  ripple?: boolean;
  autoFocus?: boolean;
  loading?: boolean;
  loadingIcon?: ReactNode;
  inputProps?: React.InputHTMLAttributes<HTMLInputElement>;
  inputRef?: RefObject<HTMLInputElement>;
  containerRef?: RefObject<HTMLLabelElement>;
  wrapperClassName?: string;
  inputClassName?: string;
  switchClassName?: string;
  trackClassName?: string;
  thumbClassName?: string;
  labelClassName?: string;
  onLabelClassName?: string;
  offLabelClassName?: string;
}

// Supporting option types
export interface CheckboxOption {
  value: unknown;
  label: ReactNode;
  disabled?: boolean;
  checked?: boolean;
  indeterminate?: boolean;
}

export interface RadioOption {
  value: unknown;
  label: ReactNode;
  disabled?: boolean;
  checked?: boolean;
}