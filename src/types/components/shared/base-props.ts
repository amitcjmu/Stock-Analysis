/**
 * Base Component Props
 * 
 * Fundamental component prop interfaces used across all components.
 */

import { ReactNode, RefObject } from 'react';

// Base shared component types
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
  id?: string;
  style?: React.CSSProperties;
  'data-testid'?: string;
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  role?: string;
  tabIndex?: number;
  onFocus?: (event: React.FocusEvent) => void;
  onBlur?: (event: React.FocusEvent) => void;
  onKeyDown?: (event: React.KeyboardEvent) => void;
  onKeyUp?: (event: React.KeyboardEvent) => void;
  onMouseEnter?: (event: React.MouseEvent) => void;
  onMouseLeave?: (event: React.MouseEvent) => void;
  onClick?: (event: React.MouseEvent) => void;
  onDoubleClick?: (event: React.MouseEvent) => void;
  onContextMenu?: (event: React.MouseEvent) => void;
}

export interface InteractiveComponentProps extends BaseComponentProps {
  disabled?: boolean;
  loading?: boolean;
  readonly?: boolean;
  required?: boolean;
  invalid?: boolean;
  error?: string | null;
  warning?: string | null;
  success?: boolean;
  tooltip?: string;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: string;
  color?: string;
  theme?: 'light' | 'dark' | 'auto';
}

export interface ContainerComponentProps extends BaseComponentProps {
  padding?: number | string;
  margin?: number | string;
  width?: number | string;
  height?: number | string;
  minWidth?: number | string;
  minHeight?: number | string;
  maxWidth?: number | string;
  maxHeight?: number | string;
  overflow?: 'visible' | 'hidden' | 'scroll' | 'auto';
  position?: 'static' | 'relative' | 'absolute' | 'fixed' | 'sticky';
  zIndex?: number;
  background?: string;
  border?: string;
  borderRadius?: number | string;
  shadow?: boolean | string;
  responsive?: boolean;
  breakpoint?: string;
}