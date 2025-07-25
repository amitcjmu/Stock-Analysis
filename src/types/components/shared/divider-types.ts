/**
 * Divider Component Types
 *
 * Divider and separator component interfaces.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from './base-props';

// Divider component types
export interface DividerProps extends BaseComponentProps {
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'dotted' | 'double';
  color?: string;
  thickness?: number;
  length?: number | string;
  spacing?: number | string;
  children?: ReactNode;
  textAlign?: 'left' | 'center' | 'right';
  absolute?: boolean;
  inset?: boolean;
  flexItem?: boolean;
  light?: boolean;
  component?: keyof JSX.IntrinsicElements | React.ComponentType<DividerProps>;
}
