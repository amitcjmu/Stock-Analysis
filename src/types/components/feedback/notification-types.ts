/**
 * Notification and Toast Component Types
 * 
 * Type definitions for notification, toast, and badge components.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

// Position types
export type NotificationPosition = 
  | 'top-left' 
  | 'top-center' 
  | 'top-right' 
  | 'middle-left' 
  | 'middle-center' 
  | 'middle-right' 
  | 'bottom-left' 
  | 'bottom-center' 
  | 'bottom-right';

export type ToastPosition = 
  | 'top-left' 
  | 'top-center' 
  | 'top-right' 
  | 'bottom-left' 
  | 'bottom-center' 
  | 'bottom-right';

// Animation types
export type NotificationAnimation = 
  | 'slide' 
  | 'fade' 
  | 'scale' 
  | 'bounce' 
  | 'flip' 
  | 'zoom' 
  | 'none';

export type ToastAnimation = 
  | 'slide' 
  | 'fade' 
  | 'scale' 
  | 'bounce' 
  | 'flip' 
  | 'zoom' 
  | 'none';

// Transition interfaces
export interface NotificationTransition {
  enter?: string;
  exit?: string;
  duration?: number;
}

export interface ToastTransition {
  enter?: string;
  exit?: string;
  duration?: number;
}

// Notification component types
export interface NotificationProps extends BaseComponentProps {
  id?: string;
  type?: 'info' | 'success' | 'warning' | 'error' | 'loading';
  title?: ReactNode;
  message?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  avatar?: ReactNode;
  image?: string;
  duration?: number;
  closable?: boolean;
  closeIcon?: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
  actionText?: string;
  onActionClick?: () => void;
  position?: NotificationPosition;
  animation?: NotificationAnimation;
  pauseOnHover?: boolean;
  pauseOnFocusLoss?: boolean;
  closeOnClick?: boolean;
  showProgress?: boolean;
  progress?: number;
  progressColor?: string;
  timestamp?: string;
  showTimestamp?: boolean;
  formatTimestamp?: (timestamp: string) => string;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  category?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  sound?: boolean;
  soundUrl?: string;
  vibrate?: boolean;
  vibratePattern?: number[];
  badge?: boolean;
  badgeText?: string;
  badgeColor?: string;
  clickThrough?: boolean;
  requireInteraction?: boolean;
  silent?: boolean;
  renotify?: boolean;
  tag?: string;
  data?: unknown;
  onShow?: () => void;
  onHide?: () => void;
  onClick?: () => void;
  onError?: (error: Error) => void;
  onPermissionChange?: (permission: NotificationPermission) => void;
  theme?: 'light' | 'dark' | 'auto';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'filled' | 'outlined' | 'standard' | 'card';
  rounded?: boolean;
  shadow?: boolean;
  bordered?: boolean;
  iconClassName?: string;
  titleClassName?: string;
  messageClassName?: string;
  descriptionClassName?: string;
  actionClassName?: string;
  closeButtonClassName?: string;
  progressClassName?: string;
  timestampClassName?: string;
  avatarClassName?: string;
  imageClassName?: string;
}

export interface NotificationContainerProps extends BaseComponentProps {
  position?: NotificationPosition;
  limit?: number;
  newestOnTop?: boolean;
  reverseOrder?: boolean;
  gutter?: number;
  containerStyle?: React.CSSProperties;
  toastStyle?: React.CSSProperties;
  bodyStyle?: React.CSSProperties;
  closeButtonStyle?: React.CSSProperties;
  progressStyle?: React.CSSProperties;
  rtl?: boolean;
  transition?: NotificationTransition;
  hideProgressBar?: boolean;
  pauseOnHover?: boolean;
  pauseOnFocusLoss?: boolean;
  closeOnClick?: boolean;
  autoClose?: boolean;
  closeButton?: boolean | ReactNode;
  icon?: boolean | ReactNode;
  theme?: 'light' | 'dark' | 'colored' | 'auto';
  enableMultiContainer?: boolean;
  containerId?: string;
  style?: React.CSSProperties;
  toastClassName?: string;
  bodyClassName?: string;
  progressClassName?: string;
  closeButtonClassName?: string;
}

// Toast component types
export interface ToastProps extends Omit<BaseComponentProps, 'id'> {
  id?: string | number;
  type?: 'info' | 'success' | 'warning' | 'error' | 'loading' | 'default';
  title?: ReactNode;
  message?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  duration?: number;
  closable?: boolean;
  closeIcon?: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
  actionText?: string;
  onActionClick?: () => void;
  position?: ToastPosition;
  animation?: ToastAnimation;
  pauseOnHover?: boolean;
  pauseOnFocusLoss?: boolean;
  closeOnClick?: boolean;
  showProgress?: boolean;
  progress?: number;
  progressColor?: string;
  hideProgressBar?: boolean;
  newestOnTop?: boolean;
  rtl?: boolean;
  limit?: number;
  role?: 'alert' | 'status';
  toastId?: string | number;
  updateId?: string | number;
  data?: unknown;
  containerId?: string;
  onOpen?: () => void;
  onUpdate?: () => void;
  theme?: 'light' | 'dark' | 'colored' | 'auto';
  transition?: ToastTransition;
  style?: React.CSSProperties;
  bodyStyle?: React.CSSProperties;
  progressStyle?: React.CSSProperties;
  closeButtonStyle?: React.CSSProperties;
  toastClassName?: string;
  bodyClassName?: string;
  progressClassName?: string;
  closeButtonClassName?: string;
  autoClose?: boolean | number;
  isLoading?: boolean;
  draggable?: boolean;
  draggablePercent?: number;
  draggableDirection?: 'x' | 'y';
  enableMultiContainer?: boolean;
  onClick?: (event: React.MouseEvent) => void;
  onDoubleClick?: (event: React.MouseEvent) => void;
}

// Badge component types
export interface BadgeProps extends BaseComponentProps {
  count?: number | ReactNode;
  showZero?: boolean;
  overflowCount?: number;
  dot?: boolean;
  status?: 'success' | 'processing' | 'default' | 'error' | 'warning';
  color?: string;
  text?: ReactNode;
  size?: 'default' | 'small';
  offset?: [number, number];
  title?: string;
  placement?: 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight';
  className?: string;
  style?: React.CSSProperties;
  children?: ReactNode;
}

// Hook types
export interface UseNotificationReturn {
  show: (notification: Omit<NotificationProps, 'id'>) => string;
  hide: (id: string) => void;
  hideAll: () => void;
  update: (id: string, updates: Partial<NotificationProps>) => void;
  notifications: NotificationProps[];
  count: number;
}

export interface UseToastReturn {
  show: (toast: Omit<ToastProps, 'id'>) => string;
  hide: (id: string | number) => void;
  hideAll: () => void;
  update: (id: string | number, updates: Partial<ToastProps>) => void;
  promise: <T>(
    promise: Promise<T>,
    options: {
      loading?: ReactNode;
      success?: ReactNode | ((data: T) => ReactNode);
      error?: ReactNode | ((error: Error) => ReactNode);
    }
  ) => Promise<T>;
  success: (message: ReactNode, options?: Partial<ToastProps>) => string;
  error: (message: ReactNode, options?: Partial<ToastProps>) => string;
  warning: (message: ReactNode, options?: Partial<ToastProps>) => string;
  info: (message: ReactNode, options?: Partial<ToastProps>) => string;
  loading: (message: ReactNode, options?: Partial<ToastProps>) => string;
  dismiss: (id?: string | number) => void;
  toasts: ToastProps[];
  count: number;
}

// Configuration types
export interface NotificationConfig {
  position?: NotificationPosition;
  duration?: number;
  maxCount?: number;
  animation?: NotificationAnimation;
  pauseOnHover?: boolean;
  closeOnClick?: boolean;
  showProgress?: boolean;
  rtl?: boolean;
  theme?: 'light' | 'dark' | 'auto';
  containerStyle?: React.CSSProperties;
  notificationStyle?: React.CSSProperties;
}

export interface ToastConfig {
  position?: ToastPosition;
  duration?: number;
  maxCount?: number;
  animation?: ToastAnimation;
  pauseOnHover?: boolean;
  closeOnClick?: boolean;
  showProgress?: boolean;
  rtl?: boolean;
  theme?: 'light' | 'dark' | 'colored' | 'auto';
  containerStyle?: React.CSSProperties;
  toastStyle?: React.CSSProperties;
}