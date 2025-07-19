/**
 * List Component Types
 * 
 * Type definitions for list components including list items, pagination,
 * search, filtering, sorting, and list configuration options.
 */

import { ReactNode } from 'react';
import { BaseComponentProps, InteractiveComponentProps } from '../shared';

// Basic list data types
export interface ListItemData {
  id?: string | number;
  [key: string]: unknown;
}

export interface ListProps<TData extends ListItemData = ListItemData> extends BaseComponentProps {
  data: TData[];
  loading?: boolean;
  error?: string | null;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'bordered' | 'divided' | 'card' | 'inline';
  bordered?: boolean;
  divided?: boolean;
  striped?: boolean;
  hover?: boolean;
  selectable?: boolean;
  multiple?: boolean;
  selectedItems?: TData[];
  onSelectionChange?: (selectedItems: TData[]) => void;
  virtualized?: boolean;
  virtualizedHeight?: number;
  virtualizedItemHeight?: number | ((index: number) => number);
  virtualizedOverscan?: number;
  estimatedItemHeight?: number;
  pagination?: ListPaginationConfig;
  search?: ListSearchConfig;
  filtering?: ListFilterConfig;
  sorting?: ListSortConfig;
  grouping?: ListGroupConfig;
  actions?: ListActionConfig;
  emptyState?: ReactNode;
  loadingState?: ReactNode;
  errorState?: ReactNode;
  header?: ReactNode;
  footer?: ReactNode;
  renderItem: (item: TData, index: number) => ReactNode;
  renderGroup?: (group: string, items: TData[]) => ReactNode;
  renderHeader?: () => ReactNode;
  renderFooter?: () => ReactNode;
  renderEmptyState?: () => ReactNode;
  renderLoadingState?: () => ReactNode;
  renderErrorState?: (error: string) => ReactNode;
  onItemClick?: (item: TData, index: number) => void;
  onItemDoubleClick?: (item: TData, index: number) => void;
  onItemContextMenu?: (item: TData, index: number, event: React.MouseEvent) => void;
  getItemId?: (item: TData, index: number) => string;
  getItemClassName?: (item: TData, index: number) => string;
  getItemStyle?: (item: TData, index: number) => React.CSSProperties;
}

export interface ListItemProps extends InteractiveComponentProps {
  selected?: boolean;
  active?: boolean;
  divider?: boolean;
  inset?: boolean;
  dense?: boolean;
  avatar?: ReactNode;
  icon?: ReactNode;
  primary?: ReactNode;
  secondary?: ReactNode;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  button?: boolean;
  href?: string;
  component?: React.ElementType;
  alignItems?: 'flex-start' | 'center';
  disableGutters?: boolean;
  disablePadding?: boolean;
  onActionClick?: (event: React.MouseEvent) => void;
  onSecondaryActionClick?: (event: React.MouseEvent) => void;
  avatarClassName?: string;
  iconClassName?: string;
  primaryClassName?: string;
  secondaryClassName?: string;
  actionClassName?: string;
  secondaryActionClassName?: string;
}

// List configuration types
export interface ListPaginationConfig {
  current?: number;
  pageSize?: number;
  total?: number;
  onChange?: (page: number, pageSize: number) => void;
  showSizeChanger?: boolean;
  pageSizeOptions?: number[];
  size?: 'small' | 'default';
  simple?: boolean;
}

export interface ListSearchConfig {
  enabled?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  searchKey?: string | string[];
  caseSensitive?: boolean;
  highlightResults?: boolean;
}

export interface ListFilterConfig {
  enabled?: boolean;
  filters?: ListFilter[];
  onChange?: (filters: Record<string, unknown>) => void;
}

export interface ListSortConfig {
  enabled?: boolean;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  onChange?: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
  options?: ListSortOption[];
}

export interface ListGroupConfig {
  enabled?: boolean;
  groupBy?: string | ((item: ListItemData) => string);
  renderGroup?: (group: string, items: ListItemData[]) => ReactNode;
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

export interface ListActionConfig {
  enabled?: boolean;
  actions?: ListAction[];
  onAction?: (action: string, item: ListItemData, index: number) => void;
  position?: 'start' | 'end';
  trigger?: 'hover' | 'always';
}

// Supporting types
export interface ListFilter {
  key: string;
  label: string;
  type: 'select' | 'multiselect' | 'range' | 'text' | 'date';
  options?: { label: string; value: unknown }[];
  value?: unknown;
}

export interface ListSortOption {
  label: string;
  value: string;
  order?: 'asc' | 'desc';
}

export interface ListAction {
  key: string;
  label: string;
  icon?: ReactNode;
  onClick?: (item: ListItemData, index: number) => void;
  disabled?: boolean | ((item: ListItemData, index: number) => boolean);
  visible?: boolean | ((item: ListItemData, index: number) => boolean);
}