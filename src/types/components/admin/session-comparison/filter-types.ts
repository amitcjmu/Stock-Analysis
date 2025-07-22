/**
 * Filter and Export Types
 * 
 * Filter, column, and export types for session comparison functionality.
 */

import { ReactNode } from 'react';
import { UserSession } from './session-types';
import { ColumnType, FilterType, FilterOperator } from './enum-types';

export interface SessionComparisonColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, sessions: UserSession[], index: number) => ReactNode;
  compareRender?: (values: unknown[], sessions: UserSession[]) => ReactNode;
  showDifferences?: boolean;
  type: ColumnType;
}

export interface SessionFilter {
  key: string;
  label: string;
  type: FilterType;
  field: string;
  operator?: FilterOperator;
  options?: FilterOption[];
  value?: unknown;
  placeholder?: string;
  validation?: ValidationRule[];
}

export interface FilterOption {
  label: string;
  value: unknown;
  disabled?: boolean;
  description?: string;
}

export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: unknown;
  message: string;
  validator?: (value: unknown) => boolean | Promise<boolean>;
}

export interface ExportFormat {
  type: 'csv' | 'excel' | 'pdf' | 'json' | 'xml';
  label: string;
  options?: ExportOptions;
}

export interface ExportOptions {
  includeMetadata?: boolean;
  includeActivities?: boolean;
  includeMetrics?: boolean;
  includeComparison?: boolean;
  compression?: boolean;
  format?: string;
}