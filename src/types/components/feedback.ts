/**
 * Feedback Component Types
 * 
 * Type definitions for feedback components including alerts, notifications,
 * loading states, progress indicators, and user feedback components.
 */

import { ReactNode } from 'react';
import { BaseComponentProps, InteractiveComponentProps } from './shared';

// Alert component types
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
  data?: any;
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
export interface ToastProps extends BaseComponentProps {
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
  data?: any;
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

// Progress component types
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

// Message component types
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

// Feedback form component types
export interface FeedbackFormProps extends BaseComponentProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  placeholder?: string;
  ratingEnabled?: boolean;
  ratingMax?: number;
  ratingLabels?: string[];
  ratingIcons?: ReactNode[];
  categoriesEnabled?: boolean;
  categories?: FeedbackCategory[];
  attachmentEnabled?: boolean;
  attachmentTypes?: string[];
  attachmentMaxSize?: number;
  attachmentMaxCount?: number;
  contactEnabled?: boolean;
  contactRequired?: boolean;
  contactFields?: ContactField[];
  anonymousEnabled?: boolean;
  defaultAnonymous?: boolean;
  screenshotEnabled?: boolean;
  screenshotAutoCapture?: boolean;
  metadata?: Record<string, any>;
  onSubmit?: (feedback: FeedbackData) => void | Promise<void>;
  onCancel?: () => void;
  onRatingChange?: (rating: number) => void;
  onCategoryChange?: (category: string) => void;
  onAttachmentAdd?: (file: File) => void;
  onAttachmentRemove?: (file: File) => void;
  onScreenshotCapture?: (screenshot: Blob) => void;
  submitText?: string;
  cancelText?: string;
  loadingText?: string;
  successText?: string;
  errorText?: string;
  loading?: boolean;
  error?: string | null;
  success?: boolean;
  disabled?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'modal' | 'drawer' | 'inline';
  position?: 'center' | 'top' | 'bottom' | 'left' | 'right';
  trigger?: ReactNode;
  triggerType?: 'click' | 'hover' | 'manual';
  autoShow?: boolean;
  showAfterDelay?: number;
  theme?: 'light' | 'dark' | 'auto';
  className?: string;
  style?: React.CSSProperties;
  formClassName?: string;
  titleClassName?: string;
  subtitleClassName?: string;
  contentClassName?: string;
  actionsClassName?: string;
}

// Supporting types
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

export interface ProgressGradient {
  from: string;
  to: string;
  direction?: string;
}

export interface ProgressSuccessProps {
  percent?: number;
  strokeColor?: string;
}

export interface FeedbackCategory {
  id: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  color?: string;
}

export interface ContactField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'tel' | 'url';
  required?: boolean;
  placeholder?: string;
  validation?: {
    pattern?: RegExp;
    minLength?: number;
    maxLength?: number;
    message?: string;
  };
}

export interface FeedbackData {
  rating?: number;
  category?: string;
  message: string;
  attachments?: File[];
  screenshot?: Blob;
  contact?: Record<string, string>;
  anonymous: boolean;
  metadata?: Record<string, any>;
  timestamp: string;
  userAgent?: string;
  url?: string;
  userId?: string;
  sessionId?: string;
}

// Hook types for feedback components
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

export interface UseAlertReturn {
  show: (alert: Omit<AlertProps, 'id'>) => string;
  hide: (id: string) => void;
  hideAll: () => void;
  update: (id: string, updates: Partial<AlertProps>) => void;
  alerts: AlertProps[];
  count: number;
}

export interface UseLoadingReturn {
  loading: boolean;
  show: (options?: Partial<LoadingProps>) => void;
  hide: () => void;
  toggle: () => void;
  setLoading: (loading: boolean) => void;
}

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

export interface UseFeedbackReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  submit: (feedback: FeedbackData) => Promise<void>;
  reset: () => void;
  loading: boolean;
  error: string | null;
  success: boolean;
  data: FeedbackData | null;
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

export interface FeedbackConfig {
  enabled?: boolean;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left' | 'center';
  trigger?: 'manual' | 'auto' | 'exit-intent' | 'scroll' | 'time';
  triggerDelay?: number;
  triggerScrollPercent?: number;
  ratingEnabled?: boolean;
  categoriesEnabled?: boolean;
  attachmentEnabled?: boolean;
  contactEnabled?: boolean;
  screenshotEnabled?: boolean;
  anonymousEnabled?: boolean;
  metadata?: Record<string, any>;
  apiEndpoint?: string;
  apiHeaders?: Record<string, string>;
  theme?: 'light' | 'dark' | 'auto';
  customStyles?: React.CSSProperties;
}