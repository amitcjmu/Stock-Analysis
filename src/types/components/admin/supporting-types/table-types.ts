/**
 * Table Types
 * 
 * Table column definitions, pagination settings, and table-related
 * configuration types.
 */

import type { ReactNode } from 'react';
import type { ValidationRule } from './form-types';

export interface TableColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  minWidth?: number;
  maxWidth?: number;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  resizable?: boolean;
  fixed?: 'left' | 'right';
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, record: unknown, index: number) => ReactNode;
  headerRender?: (column: TableColumn) => ReactNode;
  filterRender?: (column: TableColumn) => ReactNode;
  sorterRender?: (column: TableColumn) => ReactNode;
  ellipsis?: boolean;
  copyable?: boolean;
  editable?: boolean;
  required?: boolean;
  validation?: ValidationRule[];
}

export interface PaginationConfig {
  page: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  pageSizeOptions?: number[];
  simple?: boolean;
}