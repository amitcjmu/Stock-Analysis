/**
 * Divider Component Types
 * 
 * Divider and separator component interfaces.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from './base-props';

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
  component?: keyof JSX.IntrinsicElements | React.ComponentType<any>;
}