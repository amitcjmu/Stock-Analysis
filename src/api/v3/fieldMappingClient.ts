/**
 * Field Mapping Client for API v3
 * Handles field mapping operations and validation
 */

import type { ApiClient } from './client';
import type {
  FieldMappingCreate,
  FieldMappingUpdate,
  FieldMappingResponse,
  FieldMappingValidation,
  FieldMappingValidationResponse,
  FieldMappingSuggestionsResponse,
  TargetSchemasResponse,
  FieldMappingListParams,
  FieldMappingListResponse,
  DataValidationRule
} from './types/fieldMapping';
import type { RequestConfig } from './types/common';

/**
 * Field Mapping API Client
 */
export class FieldMappingClient {
  constructor(private apiClient: ApiClient) {}

  /**
   * Create new field mappings for a discovery flow
   */
  async createFieldMapping(
    data: FieldMappingCreate,
    config: RequestConfig = {}
  ): Promise<FieldMappingResponse> {
    return this.apiClient.post<FieldMappingResponse>('/field-mapping/mappings', data, config);
  }

  /**
   * Get field mappings for a discovery flow
   */
  async getFieldMapping(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<FieldMappingResponse> {
    return this.apiClient.get<FieldMappingResponse>(
      `/field-mapping/mappings/${flowId}`,
      undefined,
      config
    );
  }

  /**
   * Update field mappings for a discovery flow
   */
  async updateFieldMapping(
    flowId: string,
    data: FieldMappingUpdate,
    config: RequestConfig = {}
  ): Promise<FieldMappingResponse> {
    return this.apiClient.put<FieldMappingResponse>(
      `/field-mapping/mappings/${flowId}`,
      data,
      config
    );
  }

  /**
   * Validate field mappings against sample data
   */
  async validateFieldMapping(
    flowId: string,
    validation: FieldMappingValidation,
    config: RequestConfig = {}
  ): Promise<FieldMappingValidationResponse> {
    return this.apiClient.post<FieldMappingValidationResponse>(
      `/field-mapping/mappings/${flowId}/validate`,
      validation,
      config
    );
  }

  /**
   * Delete field mappings for a discovery flow
   */
  async deleteFieldMapping(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<void> {
    return this.apiClient.delete<void>(`/field-mapping/mappings/${flowId}`, config);
  }

  /**
   * Get available target schemas for field mapping
   */
  async getTargetSchemas(
    config: RequestConfig = {}
  ): Promise<TargetSchemasResponse> {
    return this.apiClient.get<TargetSchemasResponse>('/field-mapping/schemas', undefined, config);
  }

  /**
   * Get field mapping suggestions for a specific source field
   */
  async getMappingSuggestions(
    flowId: string,
    sourceField: string,
    config: RequestConfig = {}
  ): Promise<FieldMappingSuggestionsResponse> {
    return this.apiClient.get<FieldMappingSuggestionsResponse>(
      `/field-mapping/suggestions/${flowId}`,
      { source_field: sourceField },
      config
    );
  }

  /**
   * Get field mapping suggestions for multiple fields
   */
  async getBulkMappingSuggestions(
    flowId: string,
    sourceFields: string[],
    config: RequestConfig = {}
  ): Promise<Record<string, FieldMappingSuggestionsResponse>> {
    return this.apiClient.post<Record<string, FieldMappingSuggestionsResponse>>(
      `/field-mapping/suggestions/${flowId}/bulk`,
      { source_fields: sourceFields },
      config
    );
  }

  /**
   * List field mappings with filtering and pagination
   */
  async listFieldMappings(
    params: FieldMappingListParams = {},
    config: RequestConfig = {}
  ): Promise<FieldMappingListResponse> {
    return this.apiClient.get<FieldMappingListResponse>('/field-mapping/mappings', params, config);
  }

  /**
   * Auto-map fields using AI suggestions
   */
  async autoMapFields(
    flowId: string,
    sourceFields: string[],
    targetSchema: string,
    confidenceThreshold: number = 0.7,
    config: RequestConfig = {}
  ): Promise<FieldMappingResponse> {
    return this.apiClient.post<FieldMappingResponse>(
      `/field-mapping/mappings/${flowId}/auto-map`,
      {
        source_fields: sourceFields,
        target_schema: targetSchema,
        confidence_threshold: confidenceThreshold
      },
      config
    );
  }

  /**
   * Apply field mapping template
   */
  async applyMappingTemplate(
    flowId: string,
    templateId: string,
    config: RequestConfig = {}
  ): Promise<FieldMappingResponse> {
    return this.apiClient.post<FieldMappingResponse>(
      `/field-mapping/mappings/${flowId}/apply-template`,
      { template_id: templateId },
      config
    );
  }

  /**
   * Save field mapping as template
   */
  async saveMappingTemplate(
    flowId: string,
    templateName: string,
    description?: string,
    config: RequestConfig = {}
  ): Promise<{ template_id: string; message: string }> {
    return this.apiClient.post(
      `/field-mapping/mappings/${flowId}/save-template`,
      {
        template_name: templateName,
        description
      },
      config
    );
  }

  /**
   * Get available mapping templates
   */
  async getMappingTemplates(
    config: RequestConfig = {}
  ): Promise<Array<{
    template_id: string;
    name: string;
    description: string;
    schema_type: string;
    field_count: number;
    created_at: string;
    usage_count: number;
  }>> {
    return this.apiClient.get('/field-mapping/templates', undefined, config);
  }

  /**
   * Validate mapping against business rules
   */
  async validateBusinessRules(
    flowId: string,
    rules: DataValidationRule[],
    config: RequestConfig = {}
  ): Promise<{
    is_valid: boolean;
    rule_results: Array<{
      rule: DataValidationRule;
      passed: boolean;
      message: string;
      affected_records: number;
    }>;
    overall_score: number;
  }> {
    return this.apiClient.post(
      `/field-mapping/mappings/${flowId}/validate-rules`,
      { rules },
      config
    );
  }

  /**
   * Get field mapping analytics
   */
  async getMappingAnalytics(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<{
    mapping_quality: {
      overall_score: number;
      completeness: number;
      confidence: number;
      consistency: number;
    };
    field_analysis: Record<string, {
      mapping_confidence: number;
      data_quality: number;
      completeness_rate: number;
      unique_values: number;
      data_types: string[];
    }>;
    recommendations: Array<{
      type: 'mapping' | 'quality' | 'validation';
      priority: 'low' | 'medium' | 'high';
      message: string;
      field?: string;
      action: string;
    }>;
  }> {
    return this.apiClient.get(
      `/field-mapping/mappings/${flowId}/analytics`,
      undefined,
      config
    );
  }

  /**
   * Preview mapping results
   */
  async previewMapping(
    flowId: string,
    sampleSize: number = 10,
    config: RequestConfig = {}
  ): Promise<{
    preview_records: Array<{
      source_record: Record<string, any>;
      mapped_record: Record<string, any>;
      mapping_issues: Array<{
        field: string;
        issue: string;
        severity: 'warning' | 'error';
      }>;
    }>;
    summary: {
      total_fields: number;
      mapped_fields: number;
      unmapped_fields: number;
      mapping_issues: number;
    };
  }> {
    return this.apiClient.get(
      `/field-mapping/mappings/${flowId}/preview`,
      { sample_size: sampleSize },
      config
    );
  }

  /**
   * Export field mappings
   */
  async exportMappings(
    flowId: string,
    format: 'json' | 'csv' | 'excel' = 'json',
    config: RequestConfig = {}
  ): Promise<Blob> {
    const response = await this.apiClient.get<Response>(
      `/field-mapping/mappings/${flowId}/export`,
      { format },
      { ...config, cache: false }
    );

    return response as unknown as Blob;
  }

  /**
   * Import field mappings from file
   */
  async importMappings(
    flowId: string,
    file: File,
    config: RequestConfig = {}
  ): Promise<FieldMappingResponse> {
    return this.apiClient.upload<FieldMappingResponse>(
      `/field-mapping/mappings/${flowId}/import`,
      file,
      {},
      { timeout: 60000 }
    );
  }

  /**
   * Get field mapping health status
   */
  async getHealth(
    config: RequestConfig = {}
  ): Promise<{
    status: string;
    service: string;
    version: string;
    timestamp: string;
    components: Record<string, boolean>;
  }> {
    return this.apiClient.get('/field-mapping/health', undefined, config);
  }

  /**
   * Learn from user feedback on mappings
   */
  async submitMappingFeedback(
    flowId: string,
    feedback: {
      field_mappings: Record<string, {
        is_correct: boolean;
        suggested_mapping?: string;
        confidence?: number;
        notes?: string;
      }>;
      overall_satisfaction: number; // 1-5 scale
      comments?: string;
    },
    config: RequestConfig = {}
  ): Promise<{ message: string; learning_applied: boolean }> {
    return this.apiClient.post(
      `/field-mapping/mappings/${flowId}/feedback`,
      feedback,
      config
    );
  }

  /**
   * Get mapping confidence scores
   */
  async getMappingConfidence(
    flowId: string,
    config: RequestConfig = {}
  ): Promise<Record<string, {
    confidence_score: number;
    confidence_factors: {
      name_similarity: number;
      data_type_match: number;
      pattern_match: number;
      context_similarity: number;
      historical_accuracy: number;
    };
    risk_level: 'low' | 'medium' | 'high';
    recommendations: string[];
  }>> {
    return this.apiClient.get(
      `/field-mapping/mappings/${flowId}/confidence`,
      undefined,
      config
    );
  }
}