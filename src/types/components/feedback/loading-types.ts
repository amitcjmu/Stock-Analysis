/**
 * Loading Component Types
 * 
 * Type definitions for loading, skeleton, and spinner components.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../shared';

// Loading component types
export interface LoadingProps extends BaseComponentProps {
  loading?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  color?: string;
  thickness?: number;
  speed?: 'slow' | 'normal' | 'fast' | number;
  variant?: 'spinner' | 'dots' | 'pulse' | 'wave' | 'bars' | 'circle' | 'square' | 'bounce';
  label?: ReactNode;
  labelPosition?: 'top' | 'bottom' | 'left' | 'right';
  showLabel?: boolean;
  overlay?: boolean;
  backdrop?: boolean;
  backdropOpacity?: number;
  backdropColor?: string;
  backdropBlur?: boolean;
  zIndex?: number;
  absolute?: boolean;
  fixed?: boolean;
  center?: boolean;
  fullScreen?: boolean;
  tip?: ReactNode;
  tipPosition?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  minHeight?: number;
  spinning?: boolean;
  indicator?: ReactNode;
  wrapperClassName?: string;
  spinClassName?: string;
  dotClassName?: string;
  tipClassName?: string;
  children?: ReactNode;
}

// Skeleton component types
export interface SkeletonAvatarProps {
  size?: 'large' | 'small' | 'default' | number;
  shape?: 'circle' | 'square';
  active?: boolean;
}

export interface SkeletonParagraphProps {
  rows?: number;
  width?: number | string | Array<number | string>;
}

export interface SkeletonTitleProps {
  width?: number | string;
}

export interface SkeletonProps extends BaseComponentProps {
  loading?: boolean;
  active?: boolean;
  avatar?: boolean | SkeletonAvatarProps;
  paragraph?: boolean | SkeletonParagraphProps;
  title?: boolean | SkeletonTitleProps;
  variant?: 'text' | 'rectangular' | 'circular' | 'rounded';
  width?: number | string;
  height?: number | string;
  animation?: 'pulse' | 'wave' | 'none';
  speed?: 'slow' | 'normal' | 'fast';
  lines?: number;
  lineHeight?: number | string;
  spacing?: number | string;
  rounded?: boolean;
  borderRadius?: number | string;
  children?: ReactNode;
}

// Spinner component types
export interface SpinnerProps extends BaseComponentProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  color?: string;
  thickness?: number;
  speed?: number;
  variant?: 'spinner' | 'dots' | 'pulse' | 'bars' | 'circle' | 'square' | 'bounce' | 'wave';
  label?: string;
  emptyColor?: string;
  capIsRound?: boolean;
  trackColor?: string;
}

// Hook types
export interface UseLoadingReturn {
  loading: boolean;
  show: (options?: Partial<LoadingProps>) => void;
  hide: () => void;
  toggle: () => void;
  setLoading: (loading: boolean) => void;
}

// Configuration types
export interface LoadingConfig {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'dots' | 'pulse' | 'wave' | 'bars';
  color?: string;
  overlay?: boolean;
  backdrop?: boolean;
  backdropOpacity?: number;
  zIndex?: number;
  delay?: number;
  minDuration?: number;
  theme?: 'light' | 'dark' | 'auto';
  spinnerStyle?: React.CSSProperties;
  overlayStyle?: React.CSSProperties;
}