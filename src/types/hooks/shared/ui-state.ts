/**
 * UI State Hook Types
 * 
 * Hook interfaces for UI components including disclosure, modal, tooltip, and dropdown hooks.
 * 
 * These types provide proper typing for React hook patterns, replacing 'any' types with
 * specific interfaces and generic constraints.
 */

import type { HTMLAttributes, ButtonHTMLAttributes, KeyboardEvent } from 'react';

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
  getButtonProps: (props?: ButtonHTMLAttributes<HTMLButtonElement>) => ButtonHTMLAttributes<HTMLButtonElement>;
  getDisclosureProps: (props?: HTMLAttributes<HTMLElement>) => HTMLAttributes<HTMLElement>;
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
  getModalProps: (props?: HTMLAttributes<HTMLElement>) => HTMLAttributes<HTMLElement>;
  getOverlayProps: (props?: HTMLAttributes<HTMLDivElement>) => HTMLAttributes<HTMLDivElement>;
  getDialogProps: (props?: HTMLAttributes<HTMLDialogElement>) => HTMLAttributes<HTMLDialogElement>;
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
  getTriggerProps: (props?: HTMLAttributes<HTMLElement>) => HTMLAttributes<HTMLElement>;
  getTooltipProps: (props?: HTMLAttributes<HTMLDivElement>) => HTMLAttributes<HTMLDivElement>;
  getArrowProps: (props?: HTMLAttributes<HTMLElement>) => HTMLAttributes<HTMLElement>;
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
  onSelect?: (value: string | number) => void;
}

export interface UseDropdownReturn {
  isOpen: boolean;
  onOpen: () => void;
  onClose: () => void;
  onToggle: () => void;
  selectedIndex: number;
  setSelectedIndex: (index: number) => void;
  getTriggerProps: (props?: ButtonHTMLAttributes<HTMLButtonElement>) => ButtonHTMLAttributes<HTMLButtonElement>;
  getMenuProps: (props?: HTMLAttributes<HTMLUListElement>) => HTMLAttributes<HTMLUListElement>;
  getItemProps: (props?: HTMLAttributes<HTMLLIElement>, index?: number) => HTMLAttributes<HTMLLIElement>;
}