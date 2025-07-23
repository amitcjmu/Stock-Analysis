/**
 * Discovery Critical Attributes API Types
 * 
 * Type definitions for critical attribute management including definition,
 * validation, business rules, and quality assessment operations.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  GetRequest,
  ListResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse,
  ValidationResult,
  MultiTenantContext
} from '../shared';

// Critical Attributes APIs
export interface GetCriticalAttributesRequest extends GetRequest {
  flowId: string;
  category?: string[];
  priority?: AttributePriority[];
  mappingStatus?: AttributeMappingStatus[];
  includeBusinessRules?: boolean;
  includeValidation?: boolean;
}

export interface GetCriticalAttributesResponse extends ListResponse<CriticalAttribute> {
  data: CriticalAttribute[];
  completenessScore: number;
  missingCritical: string[];
  recommendations?: AttributeRecommendation[];
}

export interface CreateCriticalAttributeRequest extends CreateRequest<CriticalAttributeInput> {
  flowId: string;
  data: CriticalAttributeInput;
  validateDefinition?: boolean;
  checkDuplicates?: boolean;
}

export interface CreateCriticalAttributeResponse extends CreateResponse<CriticalAttribute> {
  data: CriticalAttribute;
  duplicateCheck?: DuplicateCheckResult;
  validationResult?: ValidationResult;
}

export interface UpdateCriticalAttributeRequest extends UpdateRequest<Partial<CriticalAttribute>> {
  attributeId: string;
  data: Partial<CriticalAttribute>;
  validateChanges?: boolean;
  updateMappings?: boolean;
}

export interface UpdateCriticalAttributeResponse extends UpdateResponse<CriticalAttribute> {
  data: CriticalAttribute;
  mappingUpdates?: FieldMapping[];
  validationResult?: ValidationResult;
}

export interface ValidateAttributeRequest extends BaseApiRequest {
  attributeId: string;
  context: MultiTenantContext;
  validationType?: 'definition' | 'mapping' | 'business_rules' | 'all';
  includeRecommendations?: boolean;
}

export interface ValidateAttributeResponse extends BaseApiResponse<AttributeValidationResult> {
  data: AttributeValidationResult;
  recommendations?: AttributeRecommendation[];
  autoFixSuggestions?: AutoFixSuggestion[];
}

// Critical Attribute Models
export interface CriticalAttribute {
  id: string;
  flowId: string;
  name: string;
  description: string;
  dataType: string;
  isRequired: boolean;
  defaultValue?: unknown;
  validationRules: ValidationRule[];
  mappingStatus: AttributeMappingStatus;
  sourceFields: string[];
  targetField?: string;
  businessRules: BusinessRule[];
  priority: AttributePriority;
  category: string;
  tags: string[];
  completeness: number;
  qualityScore: number;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface CriticalAttributeInput {
  name: string;
  description: string;
  dataType: string;
  isRequired: boolean;
  defaultValue?: unknown;
  validationRules?: ValidationRule[];
  businessRules?: BusinessRule[];
  priority: AttributePriority;
  category: string;
  tags?: string[];
  metadata?: Record<string, string | number | boolean | null>;
}

export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  logic: string;
  priority: number;
  enabled: boolean;
  conditions: RuleCondition[];
  actions: RuleAction[];
  metadata?: Record<string, string | number | boolean | null>;
}

export interface RuleCondition {
  field: string;
  operator: string;
  value: unknown;
  logicalOperator?: 'and' | 'or';
}

export interface RuleAction {
  type: string;
  parameters: Record<string, string | number | boolean | null>;
  description?: string;
}

export interface AttributeValidationResult extends ValidationResult {
  attributeId: string;
  mappingValidation?: ValidationResult;
  businessRuleValidation?: ValidationResult;
  completenessCheck?: CompletenessCheck;
  qualityAssessment?: QualityAssessment;
}

export interface CompletenessCheck {
  score: number;
  missing: string[];
  recommendations: string[];
}

export interface QualityAssessment {
  score: number;
  issues: QualityIssue[];
  recommendations: string[];
}

export interface QualityIssue {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affectedRecords?: number;
  suggestion?: string;
}

export interface AttributeRecommendation {
  id: string;
  attributeId: string;
  type: 'definition' | 'mapping' | 'validation' | 'business_rule';
  priority: RecommendationPriority;
  description: string;
  suggestedChanges: Record<string, string | number | boolean | null>;
  reasoning: string;
  impact: string;
  effort: ImplementationDifficulty;
}

export interface AutoFixSuggestion {
  id: string;
  type: 'auto_fix' | 'semi_auto' | 'manual';
  description: string;
  changes: Record<string, string | number | boolean | null>;
  confidence: number;
  reversible: boolean;
  testable: boolean;
}

export interface DuplicateCheckResult {
  hasDuplicates: boolean;
  duplicates: DuplicateAttribute[];
  similarAttributes: SimilarAttribute[];
}

export interface DuplicateAttribute {
  attributeId: string;
  name: string;
  similarity: number;
  differences: string[];
}

export interface SimilarAttribute {
  attributeId: string;
  name: string;
  similarity: number;
  suggestedMerge?: boolean;
}

export interface FieldMapping {
  id: string;
  flowId: string;
  sourceField: string;
  targetField: string;
  mappingType: string;
  confidence: number;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface ValidationRule {
  id: string;
  type: string;
  parameters: Record<string, string | number | boolean | null>;
  errorMessage: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

// Enums and Types
export type AttributeMappingStatus = 'mapped' | 'unmapped' | 'partially_mapped' | 'conflicted';
export type AttributePriority = 'critical' | 'high' | 'medium' | 'low';
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low' | 'optional';
export type ImplementationDifficulty = 'trivial' | 'easy' | 'moderate' | 'difficult' | 'complex';