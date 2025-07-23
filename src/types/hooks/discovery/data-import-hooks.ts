/**
 * Discovery Data Import Hook Types
 * 
 * Type definitions for data import hooks including file validation,
 * preview data, column schemas, and import statistics.
 */

import type { BaseHookParams, BaseHookReturn } from './base-hooks';

// Filter and Sort Types
export interface MappingFilter {
  field: string;
  operator: 'eq' | 'ne' | 'contains' | 'startsWith' | 'endsWith' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'not_in';
  value: unknown;
  label?: string;
  enabled?: boolean;
}

export interface MappingSortConfig {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface AttributeFilter {
  field: string;
  operator: string;
  value: unknown;
  label?: string;
  enabled?: boolean;
}

export interface AttributeSortConfig {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface ImportFilter {
  field: string;
  operator: string;
  value: unknown;
  label?: string;
  enabled?: boolean;
}

export interface ImportSortConfig {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

// Import Error and Validation Types
export interface ImportError {
  row: number;
  column: string;
  message: string;
  severity: 'error' | 'warning';
  code?: string;
  suggestion?: string;
}

export interface PreviewData {
  headers: string[];
  rows: Array<unknown[]>;
  totalRows: number;
  sampleSize: number;
  schema: ColumnSchema[];
}

export interface ColumnSchema {
  name: string;
  type: string;
  nullable: boolean;
  unique: boolean;
  examples: unknown[];
  statistics?: ColumnStatistics;
}

export interface ColumnStatistics {
  count: number;
  nullCount: number;
  uniqueCount: number;
  minValue?: unknown;
  maxValue?: unknown;
  avgValue?: unknown;
  distribution?: Record<string, number>;
}

export interface ImportValidationResult {
  isValid: boolean;
  errors: ImportError[];
  warnings: ImportError[];
  statistics: ImportStatistics;
  schema: ColumnSchema[];
}

export interface ImportStatistics {
  totalRows: number;
  validRows: number;
  invalidRows: number;
  emptyRows: number;
  duplicateRows: number;
  columns: number;
  fileSize: number;
  processedAt: string;
}

// Export Format Type
export interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  mimeType: string;
  description?: string;
  options?: Record<string, unknown>;
}