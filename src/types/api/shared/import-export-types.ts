/**
 * Import/Export API Types
 * 
 * Types for data import, export, and data transformation operations.
 */

import { BaseApiRequest, BaseApiResponse } from './base-types';
import { MultiTenantContext } from './tenant-types';
import { FilterParameter } from './query-types';

// Export/Import
export interface ExportRequest extends BaseApiRequest {
  format: ExportFormat;
  data?: ExportDataSpec;
  filters?: FilterParameter[];
  fields?: string[];
  context: MultiTenantContext;
  compression?: CompressionOptions;
  encryption?: EncryptionOptions;
  schedule?: ScheduleOptions;
}

export interface ExportResponse extends BaseApiResponse<ExportResult> {
  data: ExportResult;
  exportId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
  expiresAt?: string;
}

export interface ImportRequest extends BaseApiRequest {
  file: File;
  format: ImportFormat;
  options?: ImportOptions;
  mapping?: FieldMapping[];
  validation?: ValidationOptions;
  context: MultiTenantContext;
  dryRun?: boolean;
}

export interface ImportResponse extends BaseApiResponse<ImportResult> {
  data: ImportResult;
  importId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  validation?: ValidationResult;
  preview?: ImportPreview;
}

// Supporting types
export interface ExportDataSpec {
  type: 'query' | 'ids' | 'all';
  query?: any;
  ids?: string[];
  fields?: string[];
  relations?: string[];
}

export interface ExportResult {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  format: ExportFormat;
  downloadUrl?: string;
  size?: number;
  recordCount?: number;
  error?: string;
  createdAt: string;
  completedAt?: string;
  expiresAt?: string;
}

export interface ImportResult {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  recordsTotal: number;
  recordsProcessed: number;
  recordsSuccessful: number;
  recordsFailed: number;
  errors?: ImportError[];
  warnings?: ImportWarning[];
  createdAt: string;
  completedAt?: string;
}

export interface ImportPreview {
  headers: string[];
  sample: any[][];
  totalRows: number;
  detectedFormat: ImportFormat;
  encoding: string;
  delimiter?: string;
  quoteChar?: string;
  escapeChar?: string;
}

export interface ImportError {
  row: number;
  column?: string;
  field?: string;
  code: string;
  message: string;
  value?: any;
}

export interface ImportWarning {
  row?: number;
  column?: string;
  field?: string;
  code: string;
  message: string;
  value?: any;
  suggestion?: string;
}

export interface FieldMapping {
  source: string;
  target: string;
  transformation?: string;
  defaultValue?: any;
  required?: boolean;
  validation?: ValidationRule[];
}

export interface ValidationRule {
  type: string;
  parameters?: Record<string, any>;
  message?: string;
}

export interface ValidationOptions {
  strict?: boolean;
  skipInvalidRows?: boolean;
  maxErrors?: number;
  rules?: ValidationRule[];
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  summary?: string;
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
  value?: any;
  constraint?: any;
  path?: string;
}

export interface ValidationWarning {
  field: string;
  code: string;
  message: string;
  value?: any;
  suggestion?: string;
  path?: string;
}

export interface ImportOptions {
  delimiter?: string;
  quoteChar?: string;
  escapeChar?: string;
  encoding?: string;
  hasHeader?: boolean;
  skipRows?: number;
  batchSize?: number;
  upsert?: boolean;
  updateExisting?: boolean;
}

export interface CompressionOptions {
  enabled: boolean;
  algorithm?: 'gzip' | 'brotli' | 'deflate';
  level?: number;
}

export interface EncryptionOptions {
  enabled: boolean;
  algorithm?: string;
  keyId?: string;
  clientEncrypted?: boolean;
}

export interface ScheduleOptions {
  immediate?: boolean;
  delay?: number;
  schedule?: string; // cron expression
  timezone?: string;
  retries?: number;
  retryDelay?: number;
}

// Format types
export type ExportFormat = 'csv' | 'xlsx' | 'json' | 'xml' | 'pdf' | 'zip';
export type ImportFormat = 'csv' | 'xlsx' | 'json' | 'xml' | 'tsv';