/**
 * API v3 Types - Index
 * Re-exports all type definitions for the v3 API client
 */

export * from './common';
export * from './discovery';
export * from './fieldMapping';
export * from './responses';
export * from './fieldCompatibility';

// Re-export specific items from dataImport to avoid conflicts
export type {
  DataImportCreate,
  DataImportUpdate,
  DataImportResponse,
  DataImportListResponse,
  DataValidationResponse,
  DataPreviewResponse,
  DataImportListParams,
  FileUploadOptions,
  ValidationRequest,
  PreviewRequest,
  SupportedFileType,
  FileTypeInfo
} from './dataImport';

export { SUPPORTED_FILE_TYPES } from './dataImport';