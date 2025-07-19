/**
 * UI State Hook Types
 * 
 * Hook interfaces for UI components including disclosure, modal, tooltip, and dropdown hooks.
 */

// UI state hooks
export interface UseDisclosureParams {
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onToggle?: (isOpen: boolean) => void;
}

export interface UseDisclosureReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  getButtonProps: (props?: any) => any;
  getDisclosureProps: (props?: any) => any;
}

export interface UseModalParams {
  defaultIsOpen?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onOverlayClick?: () => void;
  onEscapeKeyDown?: (event: KeyboardEvent) => void;
}

export interface UseModalReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  getModalProps: (props?: any) => any;
  getOverlayProps: (props?: any) => any;
  getDialogProps: (props?: any) => any;
}

export interface UseTooltipParams {
  placement?: 'top' | 'bottom' | 'left' | 'right';
  offset?: number;
  delay?: number | { open?: number; close?: number };
  closeOnClick?: boolean;
  closeOnMouseDown?: boolean;
  disabled?: boolean;
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
}

export interface UseTooltipReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  getTriggerProps: (props?: any) => any;
  getTooltipProps: (props?: any) => any;
  getArrowProps: (props?: any) => any;
}

export interface UseDropdownParams {
  placement?: 'bottom-start' | 'bottom-end' | 'top-start' | 'top-end';
  offset?: number;
  closeOnSelect?: boolean;
  closeOnBlur?: boolean;
  closeOnEsc?: boolean;
  autoSelect?: boolean;
  defaultIsOpen?: boolean;
  onOpen?: () => void;
  onClose?: () => void;
  onSelect?: (value: any) => void;
}

export interface UseDropdownReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  selectedIndex: number;
  setSelectedIndex: (index: number) => void;
  getTriggerProps: (props?: any) => any;
  getMenuProps: (props?: any) => any;
  getItemProps: (props?: any, index?: number) => any;
}