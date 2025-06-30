/**
 * Data Import Types for API v3
 * TypeScript interfaces for data import operations
 */

import type { PaginatedResponse, FileUploadConfig as CommonFileUploadConfig, FileUploadProgress as CommonFileUploadProgress } from './common';

// === Request Types ===

export interface DataImportCreate {
  name: string;
  description?: string;
  source_type: string;
  data: Record<string, any>[];
  metadata?: Record<string, any>;
  auto_create_flow?: boolean;
}

export interface DataImportUpdate {
  name?: string;
  description?: string;
  metadata?: Record<string, any>;
  status?: string;
}

export interface DataValidationRule {
  field: string;
  rule_type: string;
  parameters: Record<string, any>;
  severity: 'error' | 'warning' | 'info';
}

// === Response Types ===

export interface DataImportResponse {
  import_id: string;
  name: string;
  description?: string;
  source_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  
  // Multi-tenant context
  client_account_id: string;
  engagement_id: string;
  user_id?: string;
  
  // Data statistics
  total_records: number;
  valid_records: number;
  invalid_records: number;
  processed_records: number;
  
  // Quality metrics
  data_quality_score: number;
  validation_errors: Record<string, any>[];
  validation_warnings: Record<string, any>[];
  
  // Field analysis
  field_analysis: Record<string, any>;
  suggested_mappings: Record<string, string>;
  
  // Metadata
  metadata: Record<string, any>;
  
  // Associated flow
  flow_id?: string;
}

export interface DataValidationResponse {
  is_valid: boolean;
  validation_score: number;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  
  // Detailed validation results
  field_validation: Record<string, any>;
  data_type_analysis: Record<string, any>;
  completeness_analysis: Record<string, any>;
  
  // Issues and recommendations
  validation_errors: Record<string, any>[];
  validation_warnings: Record<string, any>[];
  recommendations: string[];
}

export interface DataPreviewResponse {
  preview_data: Record<string, any>[];
  total_records: number;
  field_names: string[];
  field_types: Record<string, string>;
  sample_size: number;
  
  // Basic statistics
  numeric_fields: string[];
  text_fields: string[];
  date_fields: string[];
  
  // Data quality indicators
  completeness_rates: Record<string, number>;
  unique_value_counts: Record<string, number>;
}

// === List Types ===

export interface DataImportListParams {
  status_filter?: string;
  source_type?: string;
  page?: number;
  page_size?: number;
}

export interface DataImportListResponse {
  imports: DataImportResponse[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

// === File Upload Types ===

export interface FileUploadOptions {
  name?: string;
  description?: string;
  auto_create_flow?: boolean;
}

export interface FileUploadProgress extends CommonFileUploadProgress {
  speed?: number;
  estimated_remaining?: number;
}

export interface FileUploadConfig extends CommonFileUploadConfig {
  onComplete?: (response: DataImportResponse) => void;
}

// === Validation Types ===

export interface ValidationRequest {
  import_id: string;
  validation_rules?: DataValidationRule[];
}

export interface PreviewRequest {
  import_id: string;
  sample_size?: number;
}

// === Supported File Types ===

export enum SupportedFileType {
  JSON = 'json',
  CSV = 'csv',
  XLSX = 'xlsx',
  XLS = 'xls',
  TXT = 'txt'
}

export interface FileTypeInfo {
  extension: string;
  mimeTypes: string[];
  description: string;
  maxSize: number;
  features: string[];
}

export const SUPPORTED_FILE_TYPES: Record<SupportedFileType, FileTypeInfo> = {
  [SupportedFileType.JSON]: {
    extension: '.json',
    mimeTypes: ['application/json'],
    description: 'JSON files with structured data',
    maxSize: 50 * 1024 * 1024, // 50MB
    features: ['nested_objects', 'arrays', 'complex_types']
  },
  [SupportedFileType.CSV]: {
    extension: '.csv',
    mimeTypes: ['text/csv', 'application/csv'],
    description: 'Comma-separated values files',
    maxSize: 100 * 1024 * 1024, // 100MB
    features: ['headers', 'large_datasets', 'simple_structure']
  },
  [SupportedFileType.XLSX]: {
    extension: '.xlsx',
    mimeTypes: ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    description: 'Excel workbook files',
    maxSize: 25 * 1024 * 1024, // 25MB
    features: ['multiple_sheets', 'formatting', 'formulas']
  },
  [SupportedFileType.XLS]: {
    extension: '.xls',
    mimeTypes: ['application/vnd.ms-excel'],
    description: 'Legacy Excel files',
    maxSize: 25 * 1024 * 1024, // 25MB
    features: ['legacy_format', 'basic_structure']
  },
  [SupportedFileType.TXT]: {
    extension: '.txt',
    mimeTypes: ['text/plain'],
    description: 'Plain text files with delimited data',
    maxSize: 50 * 1024 * 1024, // 50MB
    features: ['custom_delimiters', 'simple_text']
  }
};