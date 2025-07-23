/**
 * Avatar Component Types
 * 
 * Avatar component interfaces and related types.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from './base-props';

// Avatar component types
export interface AvatarProps extends BaseComponentProps {
  src?: string;
  alt?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  variant?: 'circular' | 'rounded' | 'square';
  color?: string;
  backgroundColor?: string;
  name?: string;
  initials?: string;
  icon?: ReactNode;
  badge?: ReactNode;
  badgeColor?: string;
  badgePlacement?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  badgeOffset?: [number, number];
  fallback?: ReactNode;
  loading?: boolean;
  loadingIcon?: ReactNode;
  clickable?: boolean;
  bordered?: boolean;
  borderColor?: string;
  borderWidth?: number;
  shadow?: boolean;
  online?: boolean;
  onlineColor?: string;
  offline?: boolean;
  offlineColor?: string;
  status?: 'online' | 'offline' | 'away' | 'busy' | 'invisible';
  statusColor?: string;
  statusPlacement?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  statusSize?: number;
  group?: boolean;
  groupMax?: number;
  groupSpacing?: number;
  imgProps?: React.ImgHTMLAttributes<HTMLImageElement>;
  component?: keyof JSX.IntrinsicElements | React.ComponentType<AvatarProps>;
  onError?: (event: React.SyntheticEvent<HTMLImageElement>) => void;
  onLoad?: (event: React.SyntheticEvent<HTMLImageElement>) => void;
  onImageLoad?: () => void;
  onImageError?: () => void;
  generateInitials?: (name: string) => string;
  generateColor?: (name: string) => string;
}