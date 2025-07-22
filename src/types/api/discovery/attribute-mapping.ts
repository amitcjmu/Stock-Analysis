/**
 * Discovery Attribute Mapping API Types
 * 
 * Type definitions for attribute and field mapping operations including
 * creation, validation, approval workflows, and bulk operations.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  GetRequest,
  ListResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse,
  ValidationResult
} from '../shared';

// Attribute Mapping APIs
export interface GetFieldMappingsRequest extends GetRequest {
  flowId: string;
  dataImportId?: string;
  status?: MappingStatus[];
  mappingType?: MappingType[];
  includeValidation?: boolean;
  includeAnalysis?: boolean;
}

export interface GetFieldMappingsResponse extends ListResponse<FieldMapping> {
  data: FieldMapping[];
  statistics: MappingStatistics;
  validationSummary?: ValidationSummary;
  recommendations?: MappingRecommendation[];
}

export interface CreateFieldMappingRequest extends CreateRequest<FieldMappingInput> {
  flowId: string;
  data: FieldMappingInput;
  autoValidate?: boolean;
  generateAnalysis?: boolean;
}

export interface CreateFieldMappingResponse extends CreateResponse<FieldMapping> {
  data: FieldMapping;
  validationResult?: ValidationResult;
  analysisResult?: MappingAnalysis;
}

export interface UpdateFieldMappingRequest extends UpdateRequest<Partial<FieldMapping>> {
  mappingId: string;
  data: Partial<FieldMapping>;
  validateMapping?: boolean;
  updateAnalysis?: boolean;
}

export interface UpdateFieldMappingResponse extends UpdateResponse<FieldMapping> {
  data: FieldMapping;
  validationResult?: ValidationResult;
  analysisUpdate?: MappingAnalysis;
}

export interface BulkUpdateMappingsRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  operations: MappingOperation[];
  validateAll?: boolean;
  continueOnError?: boolean;
}

export interface BulkUpdateMappingsResponse extends BaseApiResponse<BulkMappingResult> {
  data: BulkMappingResult;
  successful: number;
  failed: number;
  validationResults?: ValidationResult[];
}

export interface ApproveMappingRequest extends BaseApiRequest {
  mappingId: string;
  context: MultiTenantContext;
  approvalComment?: string;
  autoProgress?: boolean;
}

export interface ApproveMappingResponse extends BaseApiResponse<FieldMapping> {
  data: FieldMapping;
  approved: boolean;
  flowProgressed: boolean;
  nextActions?: string[];
}

export interface RejectMappingRequest extends BaseApiRequest {
  mappingId: string;
  context: MultiTenantContext;
  rejectionReason: string;
  suggestedChanges?: string[];
  requiresManualReview?: boolean;
}

export interface RejectMappingResponse extends BaseApiResponse<FieldMapping> {
  data: FieldMapping;
  rejected: boolean;
  suggestions?: MappingRecommendation[];
  alternativeOptions?: AlternativeMapping[];
}

// Field Mapping Models
export interface FieldMapping {
  id: string;
  flowId: string;
  dataImportId: string;
  sourceField: string;
  targetField: string;
  mappingType: MappingType;
  transformationLogic?: string;
  validationRules: ValidationRule[];
  confidence: number;
  status: MappingStatus;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  reviewedBy?: string;
  rejectionReason?: string;
  analysisResult?: MappingAnalysis;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface FieldMappingInput {
  sourceField: string;
  targetField: string;
  mappingType: MappingType;
  transformationLogic?: string;
  validationRules?: ValidationRule[];
  metadata?: Record<string, string | number | boolean | null>;
}

export interface MappingStatistics {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  inReview: number;
  autoApproved: number;
  confidence: {
    high: number;
    medium: number;
    low: number;
  };
  types: Record<MappingType, number>;
}

export interface ValidationSummary {
  totalValidated: number;
  passed: number;
  failed: number;
  warnings: number;
  overallScore: number;
  criticalIssues: number;
}

export interface MappingRecommendation {
  id: string;
  mappingId: string;
  type: 'improvement' | 'alternative' | 'correction';
  confidence: number;
  description: string;
  suggestedMapping?: FieldMappingInput;
  reasoning: string;
  impact: 'low' | 'medium' | 'high';
}

export interface MappingAnalysis {
  confidence: number;
  accuracy: number;
  completeness: number;
  consistency: number;
  recommendations: string[];
  warnings: string[];
  metadata: Record<string, string | number | boolean | null>;
}

export interface MappingOperation {
  type: 'create' | 'update' | 'delete' | 'approve' | 'reject';
  mappingId?: string;
  data?: Partial<FieldMapping>;
  reason?: string;
}

export interface BulkMappingResult {
  operations: MappingOperationResult[];
  summary: {
    successful: number;
    failed: number;
    skipped: number;
  };
  validationResults: ValidationResult[];
}

export interface MappingOperationResult {
  operation: MappingOperation;
  success: boolean;
  result?: FieldMapping;
  error?: string;
  validationResult?: ValidationResult;
}

export interface AlternativeMapping {
  sourceField: string;
  targetField: string;
  confidence: number;
  reasoning: string;
  advantages: string[];
  disadvantages: string[];
}

export interface ValidationRule {
  id: string;
  type: string;
  parameters: Record<string, string | number | boolean | null>;
  errorMessage: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

// Enums and Types
export type MappingStatus = 'pending' | 'approved' | 'rejected' | 'in_review' | 'auto_approved';
export type MappingType = 'direct' | 'transformed' | 'calculated' | 'conditional' | 'lookup' | 'derived';