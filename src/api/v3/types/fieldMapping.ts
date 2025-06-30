/**
 * Field Mapping Types for API v3
 * TypeScript interfaces for field mapping operations
 */

import type { PaginatedResponse } from './common';

// === Request Types ===

export interface FieldMappingCreate {
  flow_id: string;
  source_fields: string[];
  target_schema: string;
  mapping_rules?: Record<string, any>;
  auto_map?: boolean;
}

export interface FieldMappingUpdate {
  mappings: Record<string, string>;
  confidence_scores?: Record<string, number>;
  validation_notes?: Record<string, string>;
}

export interface FieldMappingValidation {
  mappings: Record<string, string>;
  sample_data?: Record<string, any>[];
}

export interface DataValidationRule {
  field: string;
  rule_type: string;
  parameters: Record<string, any>;
  severity: 'error' | 'warning' | 'info';
}

// === Response Types ===

export interface FieldMappingResponse {
  flow_id: string;
  mapping_id: string;
  status: string;
  mappings: Record<string, string>;
  confidence_scores: Record<string, number>;
  unmapped_fields: string[];
  validation_results: Record<string, any>;
  agent_insights: Record<string, any>[];
  created_at: string;
  updated_at: string;
  
  // Statistics
  total_fields: number;
  mapped_fields: number;
  mapping_percentage: number;
  avg_confidence: number;
}

export interface FieldMappingValidationResponse {
  is_valid: boolean;
  validation_score: number;
  issues: Record<string, any>[];
  recommendations: string[];
  field_coverage: Record<string, any>;
  data_type_conflicts: Record<string, any>[];
}

export interface FieldMappingSuggestion {
  target: string;
  confidence: number;
  reason: string;
}

export interface FieldMappingSuggestionsResponse {
  source_field: string;
  suggestions: FieldMappingSuggestion[];
  auto_mapping_available: boolean;
}

// === Schema Types ===

export interface TargetFieldSchema {
  type: string;
  required: boolean;
  description: string;
}

export interface TargetSchema {
  description: string;
  fields: Record<string, TargetFieldSchema>;
}

export interface TargetSchemasResponse {
  schemas: Record<string, TargetSchema>;
}

// === List Types ===

export interface FieldMappingListParams {
  flow_id?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export type FieldMappingListResponse = PaginatedResponse<FieldMappingResponse>;