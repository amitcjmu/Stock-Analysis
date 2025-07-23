/**
 * Alert Component Types
 * 
 * Type definitions for alert components and their variants.
 */

import type { ReactNode } from 'react';
import type { BaseComponentProps } from '../shared';

export interface AlertProps extends BaseComponentProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  variant?: 'filled' | 'outlined' | 'standard' | 'ghost';
  title?: ReactNode;
  message?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  showIcon?: boolean;
  closable?: boolean;
  closeText?: ReactNode;
  closeIcon?: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
  banner?: boolean;
  border?: boolean;
  borderPosition?: 'top' | 'bottom' | 'left' | 'right';
  rounded?: boolean;
  shadow?: boolean;
  elevation?: number;
  animation?: boolean;
  autoClose?: boolean;
  autoCloseDelay?: number;
  persistent?: boolean;
  onAutoClose?: () => void;
  onClick?: (event: React.MouseEvent) => void;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  fullWidth?: boolean;
  centered?: boolean;
  iconClassName?: string;
  titleClassName?: string;
  messageClassName?: string;
  descriptionClassName?: string;
  actionClassName?: string;
  closeButtonClassName?: string;
}

export interface MessageProps extends BaseComponentProps {
  type?: 'info' | 'success' | 'warning' | 'error' | 'loading';
  content?: ReactNode;
  duration?: number;
  onClose?: () => void;
  icon?: ReactNode;
  key?: string | number;
  style?: React.CSSProperties;
  className?: string;
  onClick?: () => void;
}

export interface MessageContainerProps extends BaseComponentProps {
  top?: number;
  duration?: number;
  maxCount?: number;
  rtl?: boolean;
  prefixCls?: string;
  getContainer?: () => HTMLElement;
}

export interface UseAlertReturn {
  show: (alert: Omit<AlertProps, 'id'>) => string;
  hide: (id: string) => void;
  hideAll: () => void;
  update: (id: string, updates: Partial<AlertProps>) => void;
  alerts: AlertProps[];
  count: number;
}

export interface AlertConfig {
  duration?: number;
  maxCount?: number;
  position?: 'top' | 'bottom' | 'center';
  animation?: boolean;
  closable?: boolean;
  showIcon?: boolean;
  theme?: 'light' | 'dark' | 'auto';
  containerStyle?: React.CSSProperties;
  alertStyle?: React.CSSProperties;
}