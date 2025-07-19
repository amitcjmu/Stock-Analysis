/**
 * Badge and Chip Component Types
 * 
 * Badge, chip, and similar indicator component interfaces.
 */

import { ReactNode } from 'react';
import { BaseComponentProps, InteractiveComponentProps } from './base-props';

// Badge and chip component types
export interface BadgeProps extends BaseComponentProps {
  variant?: 'solid' | 'subtle' | 'outline' | 'soft';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'neutral' | string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  rounded?: boolean;
  dot?: boolean;
  pulse?: boolean;
  placement?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  offset?: [number, number];
  max?: number;
  showZero?: boolean;
  invisible?: boolean;
  overlap?: 'rectangular' | 'circular';
  anchorOrigin?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'right';
  };
  component?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
  slotProps?: {
    root?: any;
    badge?: any;
  };
}

export interface ChipProps extends InteractiveComponentProps {
  label: ReactNode;
  variant?: 'filled' | 'outlined' | 'soft';
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'neutral' | string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  rounded?: boolean;
  clickable?: boolean;
  deletable?: boolean;
  selected?: boolean;
  icon?: ReactNode;
  avatar?: ReactNode;
  deleteIcon?: ReactNode;
  onDelete?: (event: React.MouseEvent) => void;
  onIconClick?: (event: React.MouseEvent) => void;
  onAvatarClick?: (event: React.MouseEvent) => void;
  component?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
  href?: string;
  target?: string;
  rel?: string;
  skipFocusWhenDisabled?: boolean;
  focusVisibleClassName?: string;
  iconClassName?: string;
  avatarClassName?: string;
  labelClassName?: string;
  deleteIconClassName?: string;
}