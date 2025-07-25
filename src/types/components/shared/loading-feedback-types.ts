/**
 * Loading and Feedback Component Types
 *
 * Loading indicators, progress bars, and skeleton component interfaces.
 */

import type { BaseComponentProps } from './base-props';

// Loading and feedback component types
export interface LoadingSpinnerProps extends BaseComponentProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  color?: string;
  thickness?: number;
  speed?: 'slow' | 'normal' | 'fast' | number;
  variant?: 'spinner' | 'dots' | 'pulse' | 'wave' | 'bars';
  label?: string;
  labelPosition?: 'top' | 'bottom' | 'left' | 'right';
  overlay?: boolean;
  backdrop?: boolean;
  backdropOpacity?: number;
  zIndex?: number;
  absolute?: boolean;
  center?: boolean;
}

export interface ProgressProps extends BaseComponentProps {
  value?: number;
  max?: number;
  min?: number;
  indeterminate?: boolean;
  variant?: 'linear' | 'circular';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  thickness?: number;
  color?: string;
  trackColor?: string;
  showLabel?: boolean;
  label?: string;
  labelPosition?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  formatLabel?: (value: number, max: number) => string;
  striped?: boolean;
  animated?: boolean;
  rounded?: boolean;
}

export interface SkeletonProps extends BaseComponentProps {
  variant?: 'text' | 'rectangular' | 'circular';
  width?: number | string;
  height?: number | string;
  animation?: 'pulse' | 'wave' | 'none';
  speed?: 'slow' | 'normal' | 'fast';
  lines?: number;
  lineHeight?: number | string;
  spacing?: number | string;
  rounded?: boolean;
  borderRadius?: number | string;
}
