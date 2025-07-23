/**
 * Discovery Data Import API Types
 * 
 * Type definitions for data import operations including file uploads,
 * data validation, processing, and import management.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  FileUploadRequest,
  FileUploadResponse,
  ValidationResult,
  PaginationInfo
} from '../shared';
import type { ExtendedValue, ParameterValue } from '../shared/value-types'
import { PrimitiveValue } from '../shared/value-types'
import type { GenericMetadata } from '../shared/metadata-types';

// Data Import APIs
export interface InitiateDataImportRequest extends FileUploadRequest {
  context: MultiTenantContext;
  flowId: string;
  importName: string;
  importDescription?: string;
  fileType: string;
  expectedSchema?: ImportSchema;
  validationRules?: ValidationRule[];
  processingOptions?: ProcessingOptions;
}

export interface InitiateDataImportResponse extends FileUploadResponse {
  importId: string;
  flowId: string;
  uploadUrl?: string;
  validationResults: ValidationResult[];
  nextSteps: string[];
}

export interface GetDataImportStatusRequest extends BaseApiRequest {
  importId: string;
  includeDetails?: boolean;
  includePreview?: boolean;
}

export interface GetDataImportStatusResponse extends BaseApiResponse<DataImportData> {
  data: DataImportData;
  processing: ProcessingStatus;
  validation: ValidationStatus;
  preview?: DataPreview;
}

export interface ProcessDataImportRequest extends BaseApiRequest {
  importId: string;
  processingOptions?: ProcessingOptions;
  validationOverrides?: ValidationOverride[];
  approvals?: string[];
}

export interface ProcessDataImportResponse extends BaseApiResponse<ProcessingResult> {
  data: ProcessingResult;
  recordsProcessed: number;
  recordsSucceeded: number;
  recordsFailed: number;
  validationIssues: ValidationIssue[];
}

export interface ListDataImportsRequest extends BaseApiRequest {
  context: MultiTenantContext;
  flowId?: string;
  status?: ImportStatus;
  pagination?: PaginationInfo;
  dateRange?: DateRange;
}

export interface ListDataImportsResponse extends BaseApiResponse<DataImportData[]> {
  data: DataImportData[];
  pagination: PaginationInfo;
  summary: ImportSummary;
}

// Data Import Models
export interface DataImportData {
  id: string;
  importId: string;
  flowId: string;
  importName: string;
  importDescription?: string;
  status: ImportStatus;
  fileInfo: FileInfo;
  processingInfo: ProcessingInfo;
  validationInfo: ValidationInfo;
  metrics: ImportMetrics;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  createdBy: string;
  metadata: Record<string, unknown>;
}

export interface ImportSchema {
  version: string;
  fields: SchemaField[];
  constraints: SchemaConstraint[];
  relationships: SchemaRelationship[];
}

export interface SchemaField {
  name: string;
  type: FieldType;
  required: boolean;
  description?: string;
  constraints?: FieldConstraint[];
  defaultValue?: PrimitiveValue;
  examples?: PrimitiveValue[];
}

export interface SchemaConstraint {
  type: ConstraintType;
  fields: string[];
  rule: string;
  message: string;
}

export interface SchemaRelationship {
  type: RelationshipType;
  sourceField: string;
  targetField: string;
  targetEntity?: string;
}

export interface ValidationRule {
  id: string;
  name: string;
  description: string;
  type: ValidationType;
  parameters: Record<string, ParameterValue>;
  severity: ValidationSeverity;
  enabled: boolean;
}

export interface ProcessingOptions {
  batchSize?: number;
  parallelism?: number;
  retryOptions?: RetryOptions;
  transformations?: DataTransformation[];
  filters?: DataFilter[];
  deduplication?: DeduplicationOptions;
}

export interface FileInfo {
  fileName: string;
  fileSize: number;
  fileType: string;
  mimeType: string;
  encoding?: string;
  headers?: string[];
  rowCount?: number;
  columnCount?: number;
  checksum: string;
}

export interface ProcessingInfo {
  status: ProcessingStatus;
  stage: ProcessingStage;
  progress: number;
  startTime?: string;
  endTime?: string;
  totalRecords: number;
  processedRecords: number;
  successfulRecords: number;
  failedRecords: number;
  errors: ProcessingError[];
}

export interface ValidationInfo {
  status: ValidationStatus;
  rules: ValidationRule[];
  results: ValidationResult[];
  issues: ValidationIssue[];
  warnings: ValidationWarning[];
  summary: ValidationSummary;
}

export interface ImportMetrics {
  throughput: number;
  averageProcessingTime: number;
  errorRate: number;
  dataQualityScore: number;
  completenessScore: number;
  consistencyScore: number;
}

export interface ProcessingStatus {
  current: ProcessingStage;
  completed: ProcessingStage[];
  remaining: ProcessingStage[];
  estimatedTimeRemaining?: number;
}

export interface ValidationStatus {
  overall: ValidationLevel;
  byRule: Record<string, ValidationLevel>;
  criticalIssues: number;
  warningIssues: number;
}

export interface DataPreview {
  headers: string[];
  rows: Array<Array<PrimitiveValue | null>>;
  totalRows: number;
  sampleSize: number;
  statistics: ColumnStatistics[];
}

export interface ProcessingResult {
  importId: string;
  status: ProcessingStatus;
  summary: ProcessingSummary;
  outputs: ProcessingOutput[];
  artifacts: ProcessingArtifact[];
}

export interface ValidationIssue {
  id: string;
  rule: string;
  severity: ValidationSeverity;
  message: string;
  field?: string;
  row?: number;
  value?: PrimitiveValue;
  context?: GenericMetadata;
}

export interface ValidationOverride {
  issueId: string;
  action: OverrideAction;
  reason: string;
  approvedBy: string;
}

export interface ImportSummary {
  total: number;
  byStatus: Record<ImportStatus, number>;
  byType: Record<string, number>;
  totalRecords: number;
  totalSize: number;
}

export interface DateRange {
  startDate: string;
  endDate: string;
}

export interface ValidationWarning {
  id: string;
  type: WarningType;
  message: string;
  details?: string;
  field?: string;
  suggestion?: string;
}

export interface ValidationSummary {
  totalRules: number;
  passedRules: number;
  failedRules: number;
  totalIssues: number;
  criticalIssues: number;
  warningIssues: number;
  overallScore: number;
}

export interface ColumnStatistics {
  column: string;
  type: string;
  nullCount: number;
  uniqueCount: number;
  minValue?: number | string;
  maxValue?: number | string;
  averageValue?: number;
  topValues?: Array<{ value: PrimitiveValue; count: number }>;
}

export interface ProcessingSummary {
  totalRecords: number;
  successfulRecords: number;
  failedRecords: number;
  processingTime: number;
  throughput: number;
  qualityMetrics: QualityMetrics;
}

export interface ProcessingOutput {
  type: OutputType;
  format: string;
  location: string;
  size: number;
  recordCount: number;
  metadata: Record<string, unknown>;
}

export interface ProcessingArtifact {
  id: string;
  name: string;
  type: ArtifactType;
  location: string;
  size: number;
  description?: string;
}

export interface FieldConstraint {
  type: ConstraintType;
  value: unknown;
  message: string;
}

export interface RetryOptions {
  maxRetries: number;
  retryDelay: number;
  backoffMultiplier: number;
  retryOn: string[];
}

export interface DataTransformation {
  id: string;
  name: string;
  type: TransformationType;
  sourceField: string;
  targetField: string;
  parameters: Record<string, ParameterValue>;
}

export interface DataFilter {
  id: string;
  name: string;
  field: string;
  operator: FilterOperator;
  value: unknown;
  inverse?: boolean;
}

export interface DeduplicationOptions {
  enabled: boolean;
  strategy: DeduplicationStrategy;
  fields: string[];
  keepFirst?: boolean;
}

export interface ProcessingError {
  id: string;
  type: ErrorType;
  message: string;
  details?: string;
  row?: number;
  field?: string;
  value?: PrimitiveValue;
  timestamp: string;
}

export interface QualityMetrics {
  completeness: number;
  accuracy: number;
  consistency: number;
  validity: number;
  uniqueness: number;
  overall: number;
}

// Enums and Types
export type ImportStatus = 'uploading' | 'validating' | 'processing' | 'completed' | 'failed' | 'cancelled';
export type ProcessingStage = 'upload' | 'validation' | 'parsing' | 'transformation' | 'loading' | 'indexing';
export type ValidationLevel = 'pass' | 'warning' | 'error' | 'critical';
export type ValidationSeverity = 'info' | 'warning' | 'error' | 'critical';
export type ValidationType = 'format' | 'range' | 'pattern' | 'unique' | 'reference' | 'custom';
export type FieldType = 'string' | 'number' | 'integer' | 'boolean' | 'date' | 'datetime' | 'email' | 'url' | 'json';
export type ConstraintType = 'required' | 'unique' | 'range' | 'length' | 'pattern' | 'enum' | 'reference';
export type RelationshipType = 'one_to_one' | 'one_to_many' | 'many_to_one' | 'many_to_many';
export type OverrideAction = 'ignore' | 'fix' | 'approve' | 'escalate';
export type WarningType = 'data_quality' | 'performance' | 'compatibility' | 'recommendation';
export type OutputType = 'processed_data' | 'error_report' | 'quality_report' | 'statistics';
export type ArtifactType = 'log' | 'report' | 'metadata' | 'backup' | 'checkpoint';
export type TransformationType = 'map' | 'calculate' | 'format' | 'lookup' | 'conditional' | 'aggregate';
export type FilterOperator = 'equals' | 'not_equals' | 'contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'in' | 'not_in';
export type DeduplicationStrategy = 'exact_match' | 'fuzzy_match' | 'key_based' | 'similarity_threshold';
export type ErrorType = 'validation' | 'processing' | 'transformation' | 'system' | 'user';