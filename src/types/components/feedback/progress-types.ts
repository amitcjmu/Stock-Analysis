/**
 * Progress and Status Component Types
 * 
 * Type definitions for progress indicators and status components.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../shared';

// Progress component types
export interface ProgressGradient {
  from: string;
  to: string;
  direction?: string;
}

export interface ProgressSuccessProps {
  percent?: number;
  strokeColor?: string;
}

export interface ProgressProps extends BaseComponentProps {
  value?: number;
  max?: number;
  min?: number;
  buffer?: number;
  variant?: 'linear' | 'circular' | 'determinate' | 'indeterminate';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  thickness?: number;
  color?: string;
  trackColor?: string;
  bufferColor?: string;
  showValue?: boolean;
  showPercentage?: boolean;
  label?: ReactNode;
  labelPosition?: 'top' | 'bottom' | 'left' | 'right' | 'center' | 'inside';
  formatLabel?: (value: number, max: number) => ReactNode;
  striped?: boolean;
  animated?: boolean;
  rounded?: boolean;
  square?: boolean;
  strokeLinecap?: 'round' | 'butt' | 'square';
  gapDegree?: number;
  gapPosition?: 'top' | 'bottom' | 'left' | 'right';
  trailColor?: string;
  strokeColor?: string | ProgressGradient;
  strokeWidth?: number;
  steps?: number;
  success?: ProgressSuccessProps;
  format?: (percent?: number, successPercent?: number) => ReactNode;
  type?: 'line' | 'circle' | 'dashboard';
  status?: 'normal' | 'exception' | 'active' | 'success';
  showInfo?: boolean;
  width?: number;
  successPercent?: number;
  onProgressChange?: (value: number) => void;
  onComplete?: () => void;
  className?: string;
  style?: React.CSSProperties;
  trailStyle?: React.CSSProperties;
  strokeStyle?: React.CSSProperties;
  labelStyle?: React.CSSProperties;
}

// Status indicator component types
export interface StatusIndicatorProps extends BaseComponentProps {
  status: 'online' | 'offline' | 'away' | 'busy' | 'idle' | 'unknown';
  variant?: 'dot' | 'badge' | 'icon' | 'text';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: string;
  animated?: boolean;
  pulse?: boolean;
  label?: ReactNode;
  labelPosition?: 'top' | 'bottom' | 'left' | 'right';
  showLabel?: boolean;
  customColors?: Record<string, string>;
  customIcons?: Record<string, ReactNode>;
  tooltip?: boolean | string;
  tooltipPlacement?: 'top' | 'bottom' | 'left' | 'right';
  onClick?: () => void;
  onStatusChange?: (status: string) => void;
}

// Hook types
export interface UseProgressReturn {
  progress: number;
  setProgress: (progress: number) => void;
  increment: (amount?: number) => void;
  decrement: (amount?: number) => void;
  reset: () => void;
  complete: () => void;
  start: () => void;
  isComplete: boolean;
  isStarted: boolean;
}