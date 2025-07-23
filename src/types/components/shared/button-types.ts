/**
 * Button Component Types
 * 
 * Button and button group component interfaces.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps, InteractiveComponentProps } from './base-props';

// Button component types
export interface ButtonProps extends InteractiveComponentProps {
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'danger' | 'success' | 'warning';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  block?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  iconOnly?: boolean;
  loading?: boolean;
  loadingText?: string;
  loadingIcon?: ReactNode;
  href?: string;
  target?: string;
  rel?: string;
  download?: boolean | string;
  as?: keyof JSX.IntrinsicElements | React.ComponentType<ButtonProps>;
  form?: string;
  formAction?: string;
  formEncType?: string;
  formMethod?: string;
  formNoValidate?: boolean;
  formTarget?: string;
  name?: string;
  value?: string;
  autoFocus?: boolean;
  active?: boolean;
  pressed?: boolean;
  group?: boolean;
  toggle?: boolean;
  onToggle?: (pressed: boolean) => void;
  badge?: string | number;
  badgeColor?: string;
  badgePosition?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export interface ButtonGroupProps extends BaseComponentProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  attached?: boolean;
  spacing?: number | string;
  wrap?: boolean;
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline';
  disabled?: boolean;
  loading?: boolean;
  exclusive?: boolean;
  multiple?: boolean;
  value?: string | string[];
  onChange?: (value: string | string[]) => void;
  renderButton?: (button: ReactNode, index: number) => ReactNode;
}