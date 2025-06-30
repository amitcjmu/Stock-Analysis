/**
 * Data Import Client for API v3
 * Handles data import operations and file uploads
 */

import type { ApiClient } from './client';
import type {
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
  DataValidationRule,
  SupportedFileType,
  FileTypeInfo
} from './types/dataImport';
import { SUPPORTED_FILE_TYPES } from './types/dataImport';
import type { RequestConfig, FileUploadConfig } from './types/common';

/**
 * Data Import API Client
 */
export class DataImportClient {
  constructor(private apiClient: ApiClient) {}

  /**
   * Create a new data import
   */
  async createDataImport(
    data: DataImportCreate,
    config: RequestConfig = {}
  ): Promise<DataImportResponse> {
    return this.apiClient.post<DataImportResponse>('/data-import/imports', data, config);
  }

  /**
   * Upload and import data from file
   */
  async uploadDataFile(
    file: File,
    options: FileUploadOptions = {},
    uploadConfig: FileUploadConfig = {}
  ): Promise<DataImportResponse> {
    // Validate file type
    this.validateFileType(file);

    const uploadData = {
      name: options.name,
      description: options.description,
      auto_create_flow: options.auto_create_flow ?? true
    };

    return this.apiClient.upload<DataImportResponse>(
      '/data-import/imports/upload',
      file,
      uploadData,
      uploadConfig
    );
  }

  /**
   * Get data import details
   */
  async getDataImport(
    importId: string,
    config: RequestConfig = {}
  ): Promise<DataImportResponse> {
    return this.apiClient.get<DataImportResponse>(
      `/data-import/imports/${importId}`,
      undefined,
      config
    );
  }

  /**
   * Update data import
   */
  async updateDataImport(
    importId: string,
    data: DataImportUpdate,
    config: RequestConfig = {}
  ): Promise<DataImportResponse> {
    return this.apiClient.put<DataImportResponse>(
      `/data-import/imports/${importId}`,
      data,
      config
    );
  }

  /**
   * List data imports with filtering and pagination
   */
  async listDataImports(
    params: DataImportListParams = {},
    config: RequestConfig = {}
  ): Promise<DataImportListResponse> {
    return this.apiClient.get<DataImportListResponse>('/data-import/imports', params, config);
  }

  /**
   * Validate data import against rules
   */
  async validateDataImport(
    importId: string,
    validationRules?: DataValidationRule[],
    config: RequestConfig = {}
  ): Promise<DataValidationResponse> {
    const requestData: ValidationRequest = {
      import_id: importId,
      validation_rules: validationRules
    };

    return this.apiClient.post<DataValidationResponse>(
      `/data-import/imports/${importId}/validate`,
      requestData,
      config
    );
  }

  /**
   * Preview data import with sample records
   */
  async previewDataImport(
    importId: string,
    sampleSize: number = 10,
    config: RequestConfig = {}
  ): Promise<DataPreviewResponse> {
    const requestData: PreviewRequest = {
      import_id: importId,
      sample_size: sampleSize
    };

    return this.apiClient.get<DataPreviewResponse>(
      `/data-import/imports/${importId}/preview`,
      { sample_size: sampleSize },
      config
    );
  }

  /**
   * Delete data import
   */
  async deleteDataImport(
    importId: string,
    cascade: boolean = false,
    config: RequestConfig = {}
  ): Promise<void> {
    const params = cascade ? { cascade: true } : undefined;
    
    return this.apiClient.delete<void>(
      `/data-import/imports/${importId}`,
      { ...config }
    );
  }

  /**
   * Get data import statistics and metrics
   */
  async getImportStatistics(
    importId: string,
    config: RequestConfig = {}
  ): Promise<{
    data_quality: {
      overall_score: number;
      completeness: number;
      consistency: number;
      accuracy: number;
      validity: number;
    };
    field_statistics: Record<string, {
      completeness_rate: number;
      unique_values: number;
      data_type: string;
      sample_values: string[];
      issues: Array<{
        type: string;
        count: number;
        severity: 'low' | 'medium' | 'high';
      }>;
    }>;
    recommendations: Array<{
      category: 'quality' | 'mapping' | 'processing';
      priority: 'low' | 'medium' | 'high';
      message: string;
      action: string;
    }>;
  }> {
    return this.apiClient.get(
      `/data-import/imports/${importId}/statistics`,
      undefined,
      config
    );
  }

  /**
   * Process data import (run data cleansing and validation)
   */
  async processDataImport(
    importId: string,
    processingOptions: {
      auto_clean?: boolean;
      remove_duplicates?: boolean;
      standardize_formats?: boolean;
      validate_business_rules?: boolean;
      generate_insights?: boolean;
    } = {},
    config: RequestConfig = {}
  ): Promise<DataImportResponse> {
    return this.apiClient.post<DataImportResponse>(
      `/data-import/imports/${importId}/process`,
      processingOptions,
      config
    );
  }

  /**
   * Export processed data
   */
  async exportData(
    importId: string,
    format: 'json' | 'csv' | 'excel' = 'json',
    includeMetadata: boolean = false,
    config: RequestConfig = {}
  ): Promise<Blob> {
    const params = {
      format,
      include_metadata: includeMetadata
    };

    const response = await this.apiClient.get<Response>(
      `/data-import/imports/${importId}/export`,
      params,
      { ...config, cache: false }
    );

    return response as unknown as Blob;
  }

  /**
   * Get data cleansing suggestions
   */
  async getCleansingSupgestions(
    importId: string,
    config: RequestConfig = {}
  ): Promise<{
    suggestions: Array<{
      field: string;
      issue_type: string;
      description: string;
      suggested_action: string;
      confidence: number;
      affected_records: number;
      examples: Array<{
        original_value: string;
        suggested_value: string;
      }>;
    }>;
    auto_applicable: number;
    manual_review_required: number;
  }> {
    return this.apiClient.get(
      `/data-import/imports/${importId}/cleansing-suggestions`,
      undefined,
      config
    );
  }

  /**
   * Apply data cleansing suggestions
   */
  async applyCleansingRules(
    importId: string,
    rules: Array<{
      field: string;
      rule_type: string;
      parameters: Record<string, any>;
      apply_to_all: boolean;
    }>,
    config: RequestConfig = {}
  ): Promise<{
    applied_rules: number;
    records_affected: number;
    issues_resolved: number;
    processing_time: number;
    summary: Record<string, any>;
  }> {
    return this.apiClient.post(
      `/data-import/imports/${importId}/apply-cleansing`,
      { rules },
      config
    );
  }

  /**
   * Get supported file types and their configurations
   */
  getSupportedFileTypes(): Record<SupportedFileType, FileTypeInfo> {
    return SUPPORTED_FILE_TYPES;
  }

  /**
   * Validate file before upload
   */
  validateFileType(file: File): void {
    const extension = this.getFileExtension(file.name);
    const supportedExtensions = Object.values(SUPPORTED_FILE_TYPES).map(type => type.extension.slice(1));
    
    if (!supportedExtensions.includes(extension)) {
      throw new Error(
        `Unsupported file type: .${extension}. Supported types: ${supportedExtensions.map(ext => `.${ext}`).join(', ')}`
      );
    }

    // Check file size
    const fileTypeInfo = Object.values(SUPPORTED_FILE_TYPES).find(
      type => type.extension === `.${extension}`
    );
    
    if (fileTypeInfo && file.size > fileTypeInfo.maxSize) {
      const maxSizeMB = Math.round(fileTypeInfo.maxSize / (1024 * 1024));
      throw new Error(
        `File size (${Math.round(file.size / (1024 * 1024))}MB) exceeds maximum allowed size (${maxSizeMB}MB) for ${extension} files`
      );
    }
  }

  /**
   * Get file extension from filename
   */
  private getFileExtension(filename: string): string {
    const lastDotIndex = filename.lastIndexOf('.');
    return lastDotIndex > 0 ? filename.substring(lastDotIndex + 1).toLowerCase() : '';
  }

  /**
   * Batch upload multiple files
   */
  async batchUploadFiles(
    files: File[],
    options: FileUploadOptions = {},
    uploadConfig: FileUploadConfig = {}
  ): Promise<DataImportResponse[]> {
    // Validate all files first
    files.forEach(file => this.validateFileType(file));

    // Upload files in parallel with controlled concurrency
    const maxConcurrency = 3;
    const results: DataImportResponse[] = [];
    
    for (let i = 0; i < files.length; i += maxConcurrency) {
      const batch = files.slice(i, i + maxConcurrency);
      const batchPromises = batch.map(file => 
        this.uploadDataFile(file, {
          ...options,
          name: options.name ? `${options.name} - ${file.name}` : file.name
        }, uploadConfig)
      );
      
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
    }

    return results;
  }

  /**
   * Get import history for a specific source type
   */
  async getImportHistory(
    sourceType?: string,
    limit: number = 10,
    config: RequestConfig = {}
  ): Promise<Array<{
    import_id: string;
    name: string;
    source_type: string;
    status: string;
    created_at: string;
    record_count: number;
    quality_score: number;
  }>> {
    const params = {
      source_type: sourceType,
      limit
    };

    return this.apiClient.get('/data-import/imports/history', params, config);
  }

  /**
   * Compare two data imports
   */
  async compareImports(
    importId1: string,
    importId2: string,
    config: RequestConfig = {}
  ): Promise<{
    schema_comparison: {
      common_fields: string[];
      unique_to_import1: string[];
      unique_to_import2: string[];
      data_type_differences: Record<string, {
        import1_type: string;
        import2_type: string;
      }>;
    };
    data_comparison: {
      record_count_diff: number;
      quality_score_diff: number;
      common_values: Record<string, number>;
      value_differences: Record<string, {
        import1_unique: number;
        import2_unique: number;
      }>;
    };
    recommendations: string[];
  }> {
    return this.apiClient.post(
      '/data-import/imports/compare',
      {
        import_id_1: importId1,
        import_id_2: importId2
      },
      config
    );
  }

  /**
   * Get data import health status
   */
  async getHealth(
    config: RequestConfig = {}
  ): Promise<{
    status: string;
    service: string;
    version: string;
    timestamp: string;
    components: Record<string, boolean>;
    active_imports: number;
    processing_queue_size: number;
  }> {
    return this.apiClient.get('/data-import/health', undefined, config);
  }
}