/**
 * Alert and Notification Component Types
 * 
 * Alert, toast, and notification component interfaces.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from './base-props';

// Alert and notification component types
export interface AlertProps extends BaseComponentProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  severity?: 'low' | 'medium' | 'high' | 'critical';
  title?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  closable?: boolean;
  closeIcon?: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
  banner?: boolean;
  border?: boolean;
  borderPosition?: 'top' | 'bottom' | 'left' | 'right';
  filled?: boolean;
  outlined?: boolean;
  rounded?: boolean;
  shadow?: boolean;
  elevation?: number;
  animation?: boolean;
  autoClose?: boolean;
  autoCloseDelay?: number;
  persistent?: boolean;
  onAutoClose?: () => void;
  iconClassName?: string;
  titleClassName?: string;
  descriptionClassName?: string;
  actionClassName?: string;
  closeButtonClassName?: string;
}

export interface ToastProps extends BaseComponentProps {
  type?: 'info' | 'success' | 'warning' | 'error' | 'loading';
  title?: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  duration?: number;
  closable?: boolean;
  closeIcon?: ReactNode;
  onClose?: () => void;
  action?: ReactNode;
  position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
  animation?: 'slide' | 'fade' | 'scale' | 'bounce';
  pauseOnHover?: boolean;
  pauseOnFocusLoss?: boolean;
  closeOnClick?: boolean;
  newestOnTop?: boolean;
  rtl?: boolean;
  limit?: number;
  progress?: boolean;
  progressColor?: string;
  toastId?: string | number;
  updateId?: string | number;
  data?: unknown;
  role?: 'alert' | 'status';
  containerId?: string;
  onOpen?: () => void;
  hideProgressBar?: boolean;
  theme?: 'light' | 'dark' | 'colored';
  transition?: unknown;
  style?: React.CSSProperties;
  toastClassName?: string;
  bodyClassName?: string;
  progressClassName?: string;
  closeButton?: boolean | ((closeToast: () => void) => ReactNode);
}