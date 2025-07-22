/**
 * Component Props Examples
 * 
 * Examples demonstrating proper TypeScript interfaces for React component props.
 * These patterns should be followed across the discovery component types.
 */

import type { FC, ReactNode, ComponentProps, HTMLAttributes, MouseEvent, ChangeEvent } from 'react';
import type { BaseDiscoveryProps, FieldMapping } from './base-types';

// Example 1: Basic component with proper React types
export interface ExampleCardProps extends BaseDiscoveryProps {
  title: string;
  description?: string;
  variant?: 'default' | 'highlighted' | 'disabled';
  size?: 'sm' | 'md' | 'lg';
  onClick?: (event: MouseEvent<HTMLDivElement>) => void;
  onDoubleClick?: (event: MouseEvent<HTMLDivElement>) => void;
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
  actions?: ReactNode;
}

// Example 2: Generic component with proper typing
export interface GenericListProps<TItem = unknown> extends BaseDiscoveryProps {
  items: TItem[];
  renderItem: (item: TItem, index: number) => ReactNode;
  onItemSelect?: (item: TItem, index: number, event: MouseEvent<HTMLElement>) => void;
  selectedItems?: TItem[];
  onSelectionChange?: (selectedItems: TItem[]) => void;
  keyExtractor?: (item: TItem, index: number) => string;
  loading?: boolean;
  error?: string | null;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
}

// Example 3: Form component with proper event handlers
export interface SearchInputProps extends Omit<ComponentProps<'input'>, 'onChange' | 'value'> {
  value: string;
  onChange: (value: string, event: ChangeEvent<HTMLInputElement>) => void;
  onSearch?: (query: string, event?: MouseEvent<HTMLButtonElement>) => void;
  onClear?: (event: MouseEvent<HTMLButtonElement>) => void;
  placeholder?: string;
  loading?: boolean;
  error?: string | null;
  icon?: ReactNode;
  suggestions?: string[];
  onSuggestionSelect?: (suggestion: string, event: MouseEvent<HTMLLIElement>) => void;
  debounceMs?: number;
  clearable?: boolean;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Example 4: Component with complex event handling
export interface DataTableProps<TData = Record<string, unknown>> extends BaseDiscoveryProps {
  data: TData[];
  columns: Array<{
    key: keyof TData;
    header: string;
    render?: (value: unknown, row: TData, index: number) => ReactNode;
    sortable?: boolean;
    width?: number | string;
  }>;
  onRowClick?: (row: TData, index: number, event: MouseEvent<HTMLTableRowElement>) => void;
  onCellEdit?: (row: TData, column: keyof TData, newValue: unknown, oldValue: unknown) => Promise<boolean> | boolean;
  onSort?: (column: keyof TData, direction: 'asc' | 'desc', event: MouseEvent<HTMLButtonElement>) => void;
  selectable?: boolean;
  selectedRows?: TData[];
  onSelectionChange?: (selectedRows: TData[], event?: ChangeEvent<HTMLInputElement>) => void;
  pagination?: {
    page: number;
    pageSize: number;
    totalCount: number;
    onPageChange: (page: number, pageSize: number, event?: MouseEvent<HTMLButtonElement>) => void;
  };
  loading?: boolean;
  error?: string | null;
  emptyMessage?: string;
}

// Example 5: Higher-order component props
export interface WithLoadingProps {
  loading?: boolean;
  loadingText?: string;
  loadingComponent?: ReactNode;
  spinnerSize?: 'sm' | 'md' | 'lg';
}

export interface WithErrorProps {
  error?: string | Error | null;
  onErrorDismiss?: (event?: MouseEvent<HTMLButtonElement>) => void;
  errorComponent?: ReactNode;
  showErrorDetails?: boolean;
}

export interface WithRetryProps {
  onRetry?: (event?: MouseEvent<HTMLButtonElement>) => void;
  retryText?: string;
  maxRetries?: number;
  currentRetryCount?: number;
}

// Example 6: Compound component pattern
export interface ModalProps extends BaseDiscoveryProps {
  open: boolean;
  onClose: (event?: MouseEvent<HTMLButtonElement> | KeyboardEvent) => void;
  title?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closable?: boolean;
  maskClosable?: boolean;
  destroyOnClose?: boolean;
  centered?: boolean;
  zIndex?: number;
  afterClose?: () => void;
  afterOpen?: () => void;
}

export interface ModalHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  onClose?: (event: MouseEvent<HTMLButtonElement>) => void;
  closable?: boolean;
  extra?: ReactNode;
}

export interface ModalFooterProps {
  children?: ReactNode;
  actions?: ReactNode;
  cancelText?: string;
  okText?: string;
  onCancel?: (event: MouseEvent<HTMLButtonElement>) => void;
  onOk?: (event: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  cancelButtonProps?: ComponentProps<'button'>;
  okButtonProps?: ComponentProps<'button'>;
  loading?: boolean;
}

// Example 7: Field mapping specific examples using the patterns above
export interface FieldMappingCardProps extends BaseDiscoveryProps {
  mapping: FieldMapping;
  onApprove?: (mappingId: string, event: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  onReject?: (mappingId: string, reason: string, event: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
  onEdit?: (mappingId: string, event: MouseEvent<HTMLButtonElement>) => void;
  processing?: boolean;
  disabled?: boolean;
  showActions?: boolean;
  variant?: 'default' | 'approved' | 'rejected' | 'pending';
  size?: 'sm' | 'md' | 'lg';
}

// Example 8: Properly typed FC component
export type ExampleCardComponent = FC<ExampleCardProps>;
export type GenericListComponent = <TItem = unknown>(props: GenericListProps<TItem>) => ReactNode;
export type DataTableComponent = <TData = Record<string, unknown>>(props: DataTableProps<TData>) => ReactNode;

// Export the patterns for documentation
export type ComponentPropsPatterns = {
  // Always extend BaseDiscoveryProps for consistency
  BasePattern: BaseDiscoveryProps;
  
  // Use proper React event types
  EventHandlers: {
    onClick: (event: MouseEvent<HTMLElement>) => void;
    onChange: (value: string, event: ChangeEvent<HTMLInputElement>) => void;
    onSubmit: (event: React.FormEvent<HTMLFormElement>) => void;
  };
  
  // Make components generic when appropriate
  GenericComponent: <T>(props: { items: T[]; onSelect: (item: T) => void }) => ReactNode;
  
  // Use proper import type syntax
  ImportPattern: 'import type { FC, ReactNode } from "react";';
  
  // Provide comprehensive prop interfaces
  ComprehensiveProps: {
    // Required props
    data: unknown[];
    
    // Optional props with defaults
    loading?: boolean;
    disabled?: boolean;
    
    // Event handlers with proper signatures
    onAction?: (id: string, event: MouseEvent<HTMLButtonElement>) => Promise<void> | void;
    
    // Render props
    renderItem?: (item: unknown, index: number) => ReactNode;
    
    // Style props
    className?: string;
    size?: 'sm' | 'md' | 'lg';
    variant?: 'primary' | 'secondary';
    
    // Accessibility props
    'aria-label'?: string;
    'data-testid'?: string;
  };
};