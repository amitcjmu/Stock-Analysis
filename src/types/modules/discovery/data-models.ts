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
import { ValidationRule, BusinessRule, AgentInsight } from './validation-types'

/**
 * Field mapping entity
 */
export interface FieldMapping {
  id: string;
  sourceField: string;
  targetField: string;
  mappingType: 'direct' | 'transformed' | 'calculated' | 'conditional';
  transformationLogic?: string;
  validationRules?: ValidationRule[];
  confidence: number;
  status: 'pending' | 'approved' | 'rejected' | 'in_review';
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  reviewedBy?: string;
  rejectionReason?: string;
}

/**
 * Critical attribute definition
 */
export interface CriticalAttribute {
  id: string;
  name: string;
  description: string;
  dataType: string;
  isRequired: boolean;
  defaultValue?: unknown;
  validationRules: ValidationRule[];
  mappingStatus: 'mapped' | 'unmapped' | 'partially_mapped';
  sourceFields: string[];
  targetField?: string;
  businessRules?: BusinessRule[];
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
  analysisType: string;
  findings: AnalysisFinding[];
  recommendations: string[];
  confidence: number;
  executedAt: string;
  executedBy: string;
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
  totalMappings: number;
  completedMappings: number;
  pendingMappings: number;
  approvedMappings: number;
  rejectedMappings: number;
  progressPercentage: number;
  lastUpdated: string;
}

/**
 * Flow state management
 */
export interface FlowState {
  flowId: string;
  currentPhase: string;
  nextPhase?: string;
  previousPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseData: Record<string, string | number | boolean | null>;
  agentInsights: Record<string, AgentInsight[]>;
  agentProgress: Record<string, number>;
  agentStatus: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

/**
 * Discovery flow data structure
 */
export interface DiscoveryFlowData {
  id: string;
  flowId: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  flowName: string;
  flowDescription?: string;
  status: FlowStatus;
  progress: number;
  phases: PhaseCompletion;
  currentPhase: string;
  nextPhase?: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

/**
 * Data import entity
 */
export interface DataImport {
  id: string;
  flowId: string;
  fileName: string;
  fileSize: number;
  fileType: string;
  recordsTotal: number;
  recordsProcessed: number;
  recordsValid: number;
  recordsInvalid: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  errors?: ImportError[];
  uploadedAt: string;
  processedAt?: string;
  uploadedBy: string;
}

/**
 * Agent clarification request
 */
export interface AgentClarification {
  id: string;
  agentId: string;
  question: string;
  context: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'answered' | 'dismissed';
  response?: string;
  createdAt: string;
  answeredAt?: string;
}

/**
 * Training progress tracking
 */
export interface TrainingProgress {
  totalSamples: number;
  processedSamples: number;
  accuracy: number;
  lastTrainingRun: string;
  modelVersion: string;
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
  sourceField: string;
  targetField: string;
  mappingType: string;
  transformationLogic?: string;
  validationRules?: ValidationRule[];
}

/**
 * Bulk mapping update structure
 */
export interface BulkMappingUpdate {
  mappingId: string;
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
  canProceed: boolean;
}