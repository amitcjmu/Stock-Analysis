/**
 * Discovery Attribute Mapping Hook Types
 * 
 * Type definitions for attribute mapping hooks including field mappings,
 * critical attributes, and mapping configurations.
 */

import type { BaseHookParams } from './base-hooks'
import { BaseHookReturn } from './base-hooks'

// Attribute Mapping hook types
export interface UseAttributeMappingParams extends BaseHookParams {
  flowId?: string;
  dataImportId?: string;
  autoDetectFlow?: boolean;
  fallbackToSession?: boolean;
  requirePhase?: string;
  skipValidation?: boolean;
  includeConfidence?: boolean;
  confidenceThreshold?: number;
  maxSuggestions?: number;
  includeSystemGenerated?: boolean;
  includeUserModified?: boolean;
  includePreviouslyApproved?: boolean;
  includeFieldTypes?: boolean;
  includeDataTypes?: boolean;
  includeValidationRules?: boolean;
  includeBusinessRules?: boolean;
  includeTransformationRules?: boolean;
  includeAuditInfo?: boolean;
}

export interface UseAttributeMappingReturn {
  mappings: FieldMapping[];
  suggestions: MappingSuggestion[];
  confidence: MappingConfidence;
  validation: MappingValidation;
  actions: AttributeMappingActions;
  history: MappingHistory[];
  analytics: MappingAnalytics;
  templates: MappingTemplate[];
  conflicts: MappingConflict[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isSuccess: boolean;
  refetch: () => Promise<unknown>;
  applyMapping: (mapping: FieldMapping) => Promise<void>;
  rejectMapping: (mappingId: string, reason?: string) => Promise<void>;
  batchApplyMappings: (mappings: FieldMapping[]) => Promise<void>;
  suggestMapping: (sourceField: string, targetField?: string) => Promise<MappingSuggestion[]>;
  validateMapping: (mapping: FieldMapping) => Promise<MappingValidation>;
  saveTemplate: (template: MappingTemplate) => Promise<void>;
  loadTemplate: (templateId: string) => Promise<void>;
  exportMappings: (format: string) => Promise<Blob>;
  importMappings: (file: File) => Promise<void>;
  resetMappings: () => Promise<void>;
  autoMapSimilar: (threshold?: number) => Promise<void>;
  bulkApprove: (mappingIds: string[]) => Promise<void>;
  bulkReject: (mappingIds: string[], reason?: string) => Promise<void>;
  generateReport: () => Promise<MappingReport>;
  getRecommendations: () => Promise<MappingRecommendation[]>;
  updateMappingNotes: (mappingId: string, notes: string) => Promise<void>;
  setMappingPriority: (mappingId: string, priority: MappingPriority) => Promise<void>;
  getMappingDependencies: (mappingId: string) => Promise<MappingDependency[]>;
  validateMappingSet: (mappingIds: string[]) => Promise<SetValidation>;
  previewMapping: (mapping: FieldMapping) => Promise<MappingPreview>;
  testMapping: (mapping: FieldMapping, sampleData: Array<Record<string, unknown>>) => Promise<MappingTestResult>;
  compareMappings: (mappingId1: string, mappingId2: string) => Promise<MappingComparison>;
  optimizeMappings: () => Promise<OptimizationResult>;
  scheduleMapping: (mapping: FieldMapping, schedule: MappingSchedule) => Promise<void>;
  cancelMapping: (mappingId: string) => Promise<void>;
  pauseMapping: (mappingId: string) => Promise<void>;
  resumeMapping: (mappingId: string) => Promise<void>;
  retryMapping: (mappingId: string) => Promise<void>;
  getMappingLogs: (mappingId: string) => Promise<MappingLog[]>;
  getMappingMetrics: () => Promise<MappingMetrics>;
}

export interface AttributeMappingActions {
  apply: (mapping: FieldMapping) => Promise<void>;
  reject: (mappingId: string, reason?: string) => Promise<void>;
  suggest: (sourceField: string, options?: SuggestionOptions) => Promise<MappingSuggestion[]>;
  validate: (mapping: FieldMapping) => Promise<MappingValidation>;
  preview: (mapping: FieldMapping) => Promise<MappingPreview>;
  test: (mapping: FieldMapping, sampleData: Array<Record<string, unknown>>) => Promise<MappingTestResult>;
  save: (mapping: FieldMapping) => Promise<void>;
  delete: (mappingId: string) => Promise<void>;
  duplicate: (mappingId: string) => Promise<FieldMapping>;
  merge: (mappingIds: string[]) => Promise<FieldMapping>;
  split: (mappingId: string, splitConfig: SplitConfig) => Promise<FieldMapping[]>;
  reorder: (mappingIds: string[]) => Promise<void>;
  group: (mappingIds: string[], groupName: string) => Promise<void>;
  ungroup: (groupId: string) => Promise<void>;
  tag: (mappingId: string, tags: string[]) => Promise<void>;
  untag: (mappingId: string, tags: string[]) => Promise<void>;
  comment: (mappingId: string, comment: string) => Promise<void>;
  rate: (mappingId: string, rating: number) => Promise<void>;
  flag: (mappingId: string, flag: MappingFlag) => Promise<void>;
  unflag: (mappingId: string) => Promise<void>;
  archive: (mappingId: string) => Promise<void>;
  restore: (mappingId: string) => Promise<void>;
  export: (mappingIds: string[], format: string) => Promise<Blob>;
  import: (file: File, options?: ImportOptions) => Promise<ImportResult>;
  share: (mappingId: string, users: string[]) => Promise<void>;
  unshare: (mappingId: string, users: string[]) => Promise<void>;
  lock: (mappingId: string) => Promise<void>;
  unlock: (mappingId: string) => Promise<void>;
  bookmark: (mappingId: string) => Promise<void>;
  unbookmark: (mappingId: string) => Promise<void>;
  watch: (mappingId: string) => Promise<void>;
  unwatch: (mappingId: string) => Promise<void>;
  notify: (mappingId: string, message: string) => Promise<void>;
  schedule: (mappingId: string, schedule: MappingSchedule) => Promise<void>;
  unschedule: (mappingId: string) => Promise<void>;
  cancel: (mappingId: string) => Promise<void>;
  pause: (mappingId: string) => Promise<void>;
  resume: (mappingId: string) => Promise<void>;
  retry: (mappingId: string) => Promise<void>;
  reset: (mappingId: string) => Promise<void>;
  refresh: (mappingId: string) => Promise<void>;
  analyze: (mappingId: string) => Promise<MappingAnalysis>;
  optimize: (mappingId: string) => Promise<OptimizationSuggestion[]>;
  compare: (mappingId1: string, mappingId2: string) => Promise<MappingComparison>;
  diff: (mappingId1: string, mappingId2: string) => Promise<MappingDiff>;
  merge_conflicts: (mappingId: string) => Promise<ConflictResolution[]>;
  resolve_conflict: (conflictId: string, resolution: ConflictResolution) => Promise<void>;
  get_dependencies: (mappingId: string) => Promise<MappingDependency[]>;
  set_dependencies: (mappingId: string, dependencies: string[]) => Promise<void>;
  get_impact: (mappingId: string) => Promise<MappingImpact>;
  get_usage: (mappingId: string) => Promise<MappingUsage>;
  get_history: (mappingId: string) => Promise<MappingHistory[]>;
  get_logs: (mappingId: string) => Promise<MappingLog[]>;
  get_metrics: (mappingId: string) => Promise<MappingMetrics>;
  get_recommendations: (mappingId: string) => Promise<MappingRecommendation[]>;
  get_similar: (mappingId: string) => Promise<FieldMapping[]>;
  get_related: (mappingId: string) => Promise<FieldMapping[]>;
  get_alternatives: (mappingId: string) => Promise<FieldMapping[]>;
  get_suggestions: (mappingId: string) => Promise<MappingSuggestion[]>;
  get_validation: (mappingId: string) => Promise<MappingValidation>;
  get_preview: (mappingId: string) => Promise<MappingPreview>;
  get_test_results: (mappingId: string) => Promise<MappingTestResult[]>;
  get_performance: (mappingId: string) => Promise<MappingPerformance>;
  get_health: (mappingId: string) => Promise<MappingHealth>;
  get_status: (mappingId: string) => Promise<MappingStatus>;
  get_progress: (mappingId: string) => Promise<MappingProgress>;
  get_summary: (mappingId: string) => Promise<MappingSummary>;
  get_details: (mappingId: string) => Promise<MappingDetails>;
}

export interface UseFieldMappingsParams extends BaseHookParams {
  flowId?: string;
  includeInactive?: boolean;
  includeSystemGenerated?: boolean;
  sortBy?: FieldMappingSortOption;
  sortOrder?: 'asc' | 'desc';
  pageSize?: number;
  page?: number;
  searchTerm?: string;
  filters?: FieldMappingFilter[];
  groupBy?: FieldMappingGroupOption;
}

export interface UseFieldMappingsReturn extends BaseHookReturn<FieldMapping[]> {
  mappings: FieldMapping[];
  totalCount: number;
  pageInfo: PageInfo;
  filters: FieldMappingFilter[];
  sorts: FieldMappingSort[];
  groups: FieldMappingGroup[];
  actions: FieldMappingActions;
  statistics: FieldMappingStatistics;
  suggestions: MappingSuggestion[];
  conflicts: MappingConflict[];
  templates: MappingTemplate[];
  history: MappingHistory[];
  analytics: MappingAnalytics;
  createMapping: (mapping: CreateFieldMappingRequest) => Promise<FieldMapping>;
  updateMapping: (id: string, updates: Partial<FieldMapping>) => Promise<FieldMapping>;
  deleteMapping: (id: string) => Promise<void>;
  duplicateMapping: (id: string) => Promise<FieldMapping>;
  toggleMappingStatus: (id: string) => Promise<FieldMapping>;
  applyMappings: (ids: string[]) => Promise<ApplyResult>;
  validateMappings: (ids: string[]) => Promise<ValidationResult>;
  exportMappings: (ids: string[], format: ExportFormat) => Promise<Blob>;
  importMappings: (file: File, options?: ImportOptions) => Promise<ImportResult>;
  bulkUpdateMappings: (ids: string[], updates: Partial<FieldMapping>) => Promise<BulkUpdateResult>;
  searchMappings: (query: string, options?: SearchOptions) => Promise<FieldMapping[]>;
  filterMappings: (filters: FieldMappingFilter[]) => Promise<FieldMapping[]>;
  sortMappings: (sort: FieldMappingSort) => Promise<FieldMapping[]>;
  groupMappings: (groupBy: FieldMappingGroupOption) => Promise<FieldMappingGroup[]>;
  refreshMappings: () => Promise<void>;
  resetMappings: () => Promise<void>;
}

export interface UseCriticalAttributesParams extends BaseHookParams {
  flowId?: string;
  includeOptional?: boolean;
  includeDerived?: boolean;
  includeCalculated?: boolean;
  sortBy?: CriticalAttributeSortOption;
  sortOrder?: 'asc' | 'desc';
  filters?: CriticalAttributeFilter[];
  groupBy?: CriticalAttributeGroupOption;
  pageSize?: number;
  page?: number;
}

export interface UseCriticalAttributesReturn extends BaseHookReturn<CriticalAttribute[]> {
  attributes: CriticalAttribute[];
  required: CriticalAttribute[];
  optional: CriticalAttribute[];
  missing: CriticalAttribute[];
  conflicts: AttributeConflict[];
  suggestions: AttributeSuggestion[];
  validation: AttributeValidation;
  statistics: AttributeStatistics;
  actions: CriticalAttributeActions;
  templates: AttributeTemplate[];
  categories: AttributeCategory[];
  relationships: AttributeRelationship[];
  dependencies: AttributeDependency[];
  history: AttributeHistory[];
  analytics: AttributeAnalytics;
  createAttribute: (attribute: CreateCriticalAttributeRequest) => Promise<CriticalAttribute>;
  updateAttribute: (id: string, updates: Partial<CriticalAttribute>) => Promise<CriticalAttribute>;
  deleteAttribute: (id: string) => Promise<void>;
  toggleAttributeStatus: (id: string) => Promise<CriticalAttribute>;
  validateAttribute: (id: string) => Promise<AttributeValidation>;
  mapAttribute: (id: string, fieldMapping: FieldMapping) => Promise<void>;
  unmapAttribute: (id: string) => Promise<void>;
  markAsRequired: (id: string) => Promise<void>;
  markAsOptional: (id: string) => Promise<void>;
  setAttributePriority: (id: string, priority: AttributePriority) => Promise<void>;
  addAttributeTag: (id: string, tag: string) => Promise<void>;
  removeAttributeTag: (id: string, tag: string) => Promise<void>;
  createAttributeGroup: (name: string, attributeIds: string[]) => Promise<AttributeGroup>;
  addToAttributeGroup: (attributeId: string, groupId: string) => Promise<void>;
  removeFromAttributeGroup: (attributeId: string, groupId: string) => Promise<void>;
  getAttributeRecommendations: (id: string) => Promise<AttributeRecommendation[]>;
  getAttributeUsage: (id: string) => Promise<AttributeUsage>;
  getAttributeHistory: (id: string) => Promise<AttributeHistory[]>;
  exportAttributes: (ids: string[], format: ExportFormat) => Promise<Blob>;
  importAttributes: (file: File, options?: ImportOptions) => Promise<ImportResult>;
  refreshAttributes: () => Promise<void>;
  resetAttributes: () => Promise<void>;
}

// Supporting types for attribute mapping
export interface FieldMapping {
  id: string;
  sourceField: string;
  targetField: string;
  sourceFieldType: string;
  targetFieldType: string;
  confidence: number;
  status: MappingStatus;
  isRequired: boolean;
  isSystemGenerated: boolean;
  transformationRules: TransformationRule[];
  validationRules: ValidationRule[];
  businessRules: BusinessRule[];
  notes: string;
  tags: string[];
  priority: MappingPriority;
  category: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
  approvedBy?: string;
  approvedAt?: string;
  rejectedBy?: string;
  rejectedAt?: string;
  rejectionReason?: string;
  version: number;
  dependencies: string[];
  conflicts: string[];
  metadata: Record<string, unknown>;
}

export interface CriticalAttribute {
  id: string;
  name: string;
  description: string;
  type: AttributeType;
  dataType: string;
  isRequired: boolean;
  defaultValue?: unknown;
  constraints: AttributeConstraint[];
  validationRules: ValidationRule[];
  businessRules: BusinessRule[];
  category: string;
  subcategory?: string;
  priority: AttributePriority;
  tags: string[];
  synonyms: string[];
  aliases: string[];
  relatedAttributes: string[];
  dependencies: string[];
  derivedFrom: string[];
  usedBy: string[];
  examples: unknown[];
  notes: string;
  status: AttributeStatus;
  visibility: AttributeVisibility;
  source: AttributeSource;
  owner: string;
  steward: string;
  classification: DataClassification;
  sensitivityLevel: SensitivityLevel;
  retentionPeriod?: number;
  archivalRules: ArchivalRule[];
  auditTrail: AuditTrail[];
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
  version: number;
  metadata: Record<string, unknown>;
}

// Enum types
export type MappingStatus = 'pending' | 'approved' | 'rejected' | 'in_progress' | 'completed' | 'failed' | 'cancelled';
export type MappingPriority = 'low' | 'medium' | 'high' | 'critical';
export type AttributeType = 'primary_key' | 'foreign_key' | 'index' | 'data' | 'calculated' | 'derived' | 'metadata';
export type AttributePriority = 'low' | 'medium' | 'high' | 'critical';
export type AttributeStatus = 'active' | 'inactive' | 'deprecated' | 'draft' | 'pending_approval';
export type AttributeVisibility = 'public' | 'internal' | 'restricted' | 'confidential';
export type AttributeSource = 'system' | 'user' | 'imported' | 'derived' | 'calculated';
export type DataClassification = 'public' | 'internal' | 'confidential' | 'restricted' | 'top_secret';
export type SensitivityLevel = 'none' | 'low' | 'medium' | 'high' | 'very_high';
export type FieldMappingSortOption = 'name' | 'created_at' | 'updated_at' | 'priority' | 'status' | 'confidence';
export type FieldMappingGroupOption = 'status' | 'priority' | 'category' | 'created_by' | 'source_type' | 'target_type';
export type CriticalAttributeSortOption = 'name' | 'priority' | 'created_at' | 'updated_at' | 'category' | 'type';
export type CriticalAttributeGroupOption = 'category' | 'type' | 'priority' | 'status' | 'classification';

// Additional supporting interfaces
export interface MappingSuggestion {
  id: string;
  sourceField: string;
  targetField: string;
  confidence: number;
  reasoning: string;
  similarityScore: number;
  algorithm: string;
  metadata: Record<string, unknown>;
}

export interface MappingConfidence {
  overall: number;
  byCategory: Record<string, number>;
  distribution: ConfidenceDistribution;
  factors: ConfidenceFactor[];
}

export interface MappingValidation {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  score: number;
  rules: ValidationRule[];
  suggestions: ValidationSuggestion[];
}

export interface MappingHistory {
  id: string;
  mappingId: string;
  action: HistoryAction;
  changes: Record<string, unknown>;
  timestamp: string;
  userId: string;
  reason?: string;
  metadata: Record<string, unknown>;
}

export interface MappingAnalytics {
  totalMappings: number;
  completedMappings: number;
  pendingMappings: number;
  averageConfidence: number;
  successRate: number;
  processingTime: number;
  topCategories: CategoryStat[];
  trends: AnalyticsTrend[];
  insights: AnalyticsInsight[];
}

export interface MappingTemplate {
  id: string;
  name: string;
  description: string;
  mappings: FieldMapping[];
  category: string;
  tags: string[];
  isPublic: boolean;
  isSystem: boolean;
  createdBy: string;
  createdAt: string;
  usageCount: number;
  rating: number;
}

export interface MappingConflict {
  id: string;
  type: ConflictType;
  description: string;
  severity: ConflictSeverity;
  mappingIds: string[];
  suggestions: ConflictResolution[];
  status: ConflictStatus;
  createdAt: string;
  resolvedAt?: string;
  resolvedBy?: string;
}

// Additional complex types
export interface TransformationRule {
  id: string;
  name: string;
  type: TransformationType;
  expression: string;
  parameters: Record<string, unknown>;
  isActive: boolean;
}

export interface ValidationRule {
  id: string;
  name: string;
  type: ValidationType;
  expression: string;
  parameters: Record<string, unknown>;
  severity: ValidationSeverity;
  isActive: boolean;
}

export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority: number;
  isActive: boolean;
}

export interface AttributeConstraint {
  type: ConstraintType;
  value: unknown;
  message: string;
}

export interface ArchivalRule {
  id: string;
  condition: string;
  action: ArchivalAction;
  retentionPeriod: number;
  isActive: boolean;
}

export interface AuditTrail {
  id: string;
  action: AuditAction;
  timestamp: string;
  userId: string;
  changes: Record<string, unknown>;
  reason?: string;
}

// Enum types for supporting interfaces
export type ConflictType = 'duplicate_mapping' | 'type_mismatch' | 'constraint_violation' | 'business_rule_conflict';
export type ConflictSeverity = 'low' | 'medium' | 'high' | 'critical';
export type ConflictStatus = 'open' | 'in_progress' | 'resolved' | 'ignored';
export type TransformationType = 'format' | 'calculation' | 'lookup' | 'conditional' | 'aggregation';
export type ValidationType = 'format' | 'range' | 'length' | 'pattern' | 'custom';
export type ValidationSeverity = 'info' | 'warning' | 'error' | 'critical';
export type ConstraintType = 'not_null' | 'unique' | 'min_length' | 'max_length' | 'pattern' | 'range';
export type ArchivalAction = 'archive' | 'delete' | 'anonymize' | 'compress';
export type AuditAction = 'create' | 'update' | 'delete' | 'view' | 'export' | 'import';
export type HistoryAction = 'created' | 'updated' | 'deleted' | 'approved' | 'rejected' | 'applied';

// Additional utility interfaces
export interface PageInfo {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string;
  endCursor: string;
  totalCount: number;
}

export interface FieldMappingFilter {
  field: string;
  operator: FilterOperator;
  value: unknown;
}

export interface FieldMappingSort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface FieldMappingGroup {
  key: string;
  value: string;
  count: number;
  mappings: FieldMapping[];
}

export interface FieldMappingStatistics {
  total: number;
  byStatus: Record<MappingStatus, number>;
  byPriority: Record<MappingPriority, number>;
  byCategory: Record<string, number>;
  averageConfidence: number;
  completionRate: number;
}

export interface FieldMappingActions {
  create: (mapping: CreateFieldMappingRequest) => Promise<FieldMapping>;
  update: (id: string, updates: Partial<FieldMapping>) => Promise<FieldMapping>;
  delete: (id: string) => Promise<void>;
  apply: (id: string) => Promise<void>;
  validate: (id: string) => Promise<ValidationResult>;
  approve: (id: string) => Promise<void>;
  reject: (id: string, reason: string) => Promise<void>;
}

export interface CriticalAttributeActions {
  create: (attribute: CreateCriticalAttributeRequest) => Promise<CriticalAttribute>;
  update: (id: string, updates: Partial<CriticalAttribute>) => Promise<CriticalAttribute>;
  delete: (id: string) => Promise<void>;
  validate: (id: string) => Promise<AttributeValidation>;
  map: (id: string, fieldMapping: FieldMapping) => Promise<void>;
  unmap: (id: string) => Promise<void>;
}

export type FilterOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'in' | 'not_in' | 'greater_than' | 'less_than';