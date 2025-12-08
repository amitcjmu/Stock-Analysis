/**
 * Discovery Flow - Data Models Module
 *
 * Core business data models and entity definitions for the Discovery Flow.
 * Contains field mappings, critical attributes, crew analysis, and flow data structures.
 *
 * Generated with CC - Code Companion
 */

import type { ReactNode } from 'react';
import type { FlowStatus, PhaseCompletion } from './base-types';
import type { ValidationResult, ImportError } from './validation-types'
import type { ValidationRule, BusinessRule, AgentInsight } from './validation-types'

/**
 * Field mapping entity
 */
export interface FieldMapping {
  id: string;
  source_field: string;
  target_field: string;
  mapping_type: 'direct' | 'transformed' | 'calculated' | 'conditional';
  transformation_logic?: string;
  validation_rules?: ValidationRule[];
  confidence: number;
  status: 'pending' | 'approved' | 'rejected' | 'in_review';
  created_at: string;
  updated_at: string;
  created_by: string;
  reviewed_by?: string;
  rejection_reason?: string;
}

/**
 * Critical attribute definition
 */
export interface CriticalAttribute {
  id: string;
  name: string;
  description: string;
  data_type: string;
  is_required: boolean;
  default_value?: unknown;
  validation_rules: ValidationRule[];
  mapping_status: 'mapped' | 'unmapped' | 'partially_mapped';
  source_fields: string[];
  target_field?: string;
  business_rules?: BusinessRule[];
  priority: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  tags: string[];
  metadata: Record<string, string | number | boolean | null>;
}

/**
 * Crew analysis result
 */
export interface CrewAnalysis {
  id: string;
  analysis_type: string;
  findings: AnalysisFinding[];
  recommendations: string[];
  confidence: number;
  executed_at: string;
  executed_by: string;
  status: 'completed' | 'in_progress' | 'failed';
  metadata: Record<string, string | number | boolean | null>;
}

/**
 * Analysis finding structure
 */
export interface AnalysisFinding {
  type: string;
  description: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  recommendation: string;
  impact: string;
}

/**
 * Mapping progress tracking
 */
export interface MappingProgress {
  total_mappings: number;
  completed_mappings: number;
  pending_mappings: number;
  approved_mappings: number;
  rejected_mappings: number;
  progress_percentage: number;
  last_updated: string;
}

/**
 * Flow state management
 */
export interface FlowState {
  flow_id: string;
  current_phase: string;
  next_phase?: string;
  previous_phase?: string;
  phase_completion: Record<string, boolean>;
  phase_data: Record<string, string | number | boolean | null>;
  agent_insights: Record<string, AgentInsight[]>;
  agent_progress: Record<string, number>;
  agent_status: Record<string, string>;
  created_at: string;
  updated_at: string;
}

/**
 * Discovery flow data structure
 *
 * @deprecated Import from '@/types/discovery' instead.
 * This export is maintained for backward compatibility.
 * The authoritative type is defined in src/types/discovery.ts
 */
export type { DiscoveryFlowData } from '../../../discovery';

/**
 * Data import entity
 */
export interface DataImport {
  id: string;
  flow_id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  records_total: number;
  records_processed: number;
  records_valid: number;
  records_invalid: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  errors?: ImportError[];
  uploaded_at: string;
  processed_at?: string;
  uploaded_by: string;
}

/**
 * Agent clarification request
 */
export interface AgentClarification {
  id: string;
  agent_id: string;
  question: string;
  context: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'answered' | 'dismissed';
  response?: string;
  created_at: string;
  answered_at?: string;
}

/**
 * Training progress tracking
 */
export interface TrainingProgress {
  total_samples: number;
  processed_samples: number;
  accuracy: number;
  last_training_run: string;
  model_version: string;
}

/**
 * Mapping filter for search and filtering
 */
export interface MappingFilter {
  field: string;
  operator: 'eq' | 'ne' | 'contains' | 'startsWith' | 'endsWith';
  value: unknown;
}

/**
 * Field mapping input for API requests
 */
export interface FieldMappingInput {
  source_field: string;
  target_field: string;
  mapping_type: string;
  transformation_logic?: string;
  validation_rules?: ValidationRule[];
}

/**
 * Bulk mapping update structure
 */
export interface BulkMappingUpdate {
  mapping_id: string;
  updates: Partial<FieldMapping>;
}

/**
 * Mapping approval status summary
 */
export interface MappingApprovalStatus {
  total: number;
  approved: number;
  rejected: number;
  pending: number;
  can_proceed: boolean;
}
