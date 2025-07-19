/**
 * Modal and Overlay Component Types
 * 
 * Modal, tooltip, and overlay component interfaces.
 */

import { ReactNode, RefObject } from 'react';
import { BaseComponentProps } from './base-props';

// Modal and overlay component types
export interface ModalProps extends BaseComponentProps {
  open?: boolean;
  onClose?: () => void;
  onOpen?: () => void;
  closeOnEsc?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnDocumentClick?: boolean;
  showCloseButton?: boolean;
  closeButtonPosition?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  closeButtonIcon?: ReactNode;
  title?: ReactNode;
  subtitle?: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  centered?: boolean;
  scrollable?: boolean;
  backdrop?: boolean;
  backdropOpacity?: number;
  backdropBlur?: boolean;
  focusTrap?: boolean;
  restoreFocus?: boolean;
  preventScroll?: boolean;
  lockScroll?: boolean;
  zIndex?: number;
  animation?: 'fade' | 'scale' | 'slide' | 'none';
  animationDuration?: number;
  overlay?: boolean;
  overlayClassName?: string;
  contentClassName?: string;
  headerClassName?: string;
  bodyClassName?: string;
  footerClassName?: string;
  onAnimationStart?: () => void;
  onAnimationEnd?: () => void;
  onOverlayClick?: (event: React.MouseEvent) => void;
  onEscapeKeyDown?: (event: KeyboardEvent) => void;
  initialFocus?: RefObject<HTMLElement>;
  finalFocus?: RefObject<HTMLElement>;
  container?: HTMLElement | (() => HTMLElement);
  portal?: boolean;
  portalClassName?: string;
}

export interface TooltipProps extends BaseComponentProps {
  content: ReactNode;
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'top-start' | 'top-end' | 'bottom-start' | 'bottom-end' | 'left-start' | 'left-end' | 'right-start' | 'right-end';
  trigger?: 'hover' | 'focus' | 'click' | 'manual';
  delay?: number | { show: number; hide: number };
  offset?: number | [number, number];
  arrow?: boolean;
  interactive?: boolean;
  disabled?: boolean;
  open?: boolean;
  defaultOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
  maxWidth?: number | string;
  zIndex?: number;
  animation?: boolean;
  animationDuration?: number;
  theme?: 'light' | 'dark' | 'auto';
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'info' | 'success' | 'warning' | 'error';
  followCursor?: boolean;
  hideOnClick?: boolean;
  sticky?: boolean;
  boundary?: 'clippingParents' | 'document' | 'viewport' | HTMLElement;
  fallbackPlacements?: string[];
  flip?: boolean;
  preventOverflow?: boolean;
  strategy?: 'absolute' | 'fixed';
  onShow?: () => void;
  onHide?: () => void;
  onMount?: () => void;
  onUnmount?: () => void;
  reference?: RefObject<HTMLElement>;
  floating?: RefObject<HTMLElement>;
  portal?: boolean;
  portalContainer?: HTMLElement;
  middlewares?: any[];
}