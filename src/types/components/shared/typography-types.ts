/**
 * Typography Component Types
 *
 * Text and typography-related component interfaces.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from './base-props';

// Typography component types
export interface TypographyProps extends BaseComponentProps {
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2' | 'caption' | 'overline' | 'subtitle1' | 'subtitle2';
  component?: keyof JSX.IntrinsicElements;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'text' | 'muted' | string;
  align?: 'left' | 'center' | 'right' | 'justify';
  weight?: 'light' | 'normal' | 'medium' | 'semibold' | 'bold' | number;
  size?: number | string;
  lineHeight?: number | string;
  letterSpacing?: number | string;
  textTransform?: 'none' | 'capitalize' | 'uppercase' | 'lowercase';
  decoration?: 'none' | 'underline' | 'overline' | 'line-through';
  italic?: boolean;
  monospace?: boolean;
  truncate?: boolean;
  maxLines?: number;
  ellipsis?: boolean;
  wrap?: boolean;
  selectable?: boolean;
  copyable?: boolean;
  onCopy?: (text: string) => void;
  highlight?: string | string[];
  highlightColor?: string;
  link?: boolean;
  href?: string;
  target?: string;
  rel?: string;
  download?: boolean | string;
}
