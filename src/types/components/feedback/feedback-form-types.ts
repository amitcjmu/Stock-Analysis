/**
 * Feedback Form Component Types
 * 
 * Type definitions for feedback forms and user feedback components.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

// Feedback category and contact field types
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

// Feedback data structure
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

// Hook types
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