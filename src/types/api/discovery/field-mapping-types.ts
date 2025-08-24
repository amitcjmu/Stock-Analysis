/**
 * Field Mapping API Types
 *
 * TypeScript interfaces that EXACTLY match backend Pydantic models for field mappings.
 * Ensures type safety across the entire data flow from backend to frontend.
 *
 * NOTE: These types match the backend schema in:
 * - /backend/app/schemas/discovery_flow_schemas.py (FieldMappingItem, FieldMappingsResponse)
 * - /backend/app/models/data_import/mapping.py (ImportFieldMapping)
 * - /backend/app/api/v1/endpoints/unified_discovery.py (field mappings endpoint)
 */

import type {
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

// ============================================================================
// ENUMS - Shared between frontend and backend
// ============================================================================

/**
 * Field mapping status enumeration
 * Maps to backend SQLAlchemy model status values
 */
export type FieldMappingStatus =
  | 'suggested'    // AI-suggested mapping (from backend default)
  | 'approved'     // User-approved mapping
  | 'rejected'     // User-rejected mapping
  | 'pending'      // Awaiting user review
  | 'unmapped';    // No target field assigned

/**
 * Field mapping type enumeration
 * Maps to backend Pydantic FieldMappingItem.mapping_type
 */
export type FieldMappingType =
  | 'auto'         // Automatically detected (backend default)
  | 'manual'       // Manually created by user
  | 'suggested'    // AI-suggested mapping
  | 'direct'       // Direct field mapping (SQLAlchemy default)
  | 'inferred'     // Inferred from context
  | 'transformed'; // Requires transformation

/**
 * Mapping suggestion source
 * Maps to backend SQLAlchemy suggested_by field
 */
export type MappingSuggestionSource =
  | 'ai_mapper'    // AI-based mapping (backend default)
  | 'user'         // User-created
  | 'system'       // System-generated
  | 'import';      // From import process

// ============================================================================
// CORE FIELD MAPPING TYPES
// ============================================================================

/**
 * Individual field mapping item - EXACTLY matches backend FieldMappingItem
 *
 * Backend source: app/schemas/discovery_flow_schemas.py:415-432
 */
export interface FieldMappingItem {
  /** Source field name from CSV/import - matches backend source_field */
  source_field: string;

  /** Target field in system - matches backend target_field (Optional[str]) */
  target_field: string | null;

  /** Mapping confidence score [0.0-1.0] - matches backend confidence_score */
  confidence_score: number;

  /** Type of mapping - matches backend mapping_type */
  mapping_type: FieldMappingType;

  /** Transformation rule if any - matches backend transformation (Optional[str]) */
  transformation: string | null;

  /** Validation rules if any - matches backend validation_rules (Optional[str]) */
  validation_rules: string | null;
}

/**
 * Field mappings API response - EXACTLY matches backend FieldMappingsResponse
 *
 * Backend source: app/schemas/discovery_flow_schemas.py:434-453
 */
export interface FieldMappingsResponse {
  /** Operation success status - matches backend success */
  success: boolean;

  /** Discovery flow ID - matches backend flow_id */
  flow_id: string;

  /** List of field mappings - matches backend field_mappings */
  field_mappings: FieldMappingItem[];

  /** Total number of mappings - matches backend count */
  count: number;
}

/**
 * Extended field mapping with database fields - matches SQLAlchemy ImportFieldMapping
 *
 * Backend source: app/models/data_import/mapping.py:20-125
 */
export interface ImportFieldMapping {
  /** Unique identifier (UUID) */
  id: string;

  /** Data import ID (UUID) */
  data_import_id: string;

  /** Client account ID for multi-tenancy */
  client_account_id: string;

  /** Master flow ID (UUID, nullable) */
  master_flow_id: string | null;

  /** Source field name - matches source_field */
  source_field: string;

  /** Target field name - matches target_field */
  target_field: string;

  /** Match type - matches match_type from SQLAlchemy */
  match_type: FieldMappingType;

  /** Confidence score [0.0-1.0] - matches confidence_score */
  confidence_score: number | null;

  /** Mapping status - matches status */
  status: FieldMappingStatus;

  /** Who suggested the mapping - matches suggested_by */
  suggested_by: MappingSuggestionSource;

  /** Who approved the mapping - matches approved_by */
  approved_by: string | null;

  /** When mapping was approved - matches approved_at */
  approved_at: string | null;

  /** Transformation rules (JSON) - matches transformation_rules */
  transformation_rules: Record<string, unknown> | null;

  /** Created timestamp */
  created_at: string;

  /** Updated timestamp */
  updated_at: string;
}

// ============================================================================
// API REQUEST/RESPONSE TYPES
// ============================================================================

/**
 * Request to get field mappings for a flow
 */
export interface GetFieldMappingsRequest extends GetRequest {
  /** Flow ID to get mappings for */
  flow_id: string;

  /** Optional data import ID filter */
  data_import_id?: string;

  /** Filter by status values */
  status?: FieldMappingStatus[];

  /** Filter by mapping types */
  mapping_type?: FieldMappingType[];

  /** Include validation details */
  include_validation?: boolean;
}

/**
 * Request to create a new field mapping
 */
export interface CreateFieldMappingRequest extends CreateRequest<FieldMappingInput> {
  /** Flow ID to create mapping for */
  flow_id: string;

  /** Field mapping data */
  data: FieldMappingInput;

  /** Auto-validate the mapping */
  auto_validate?: boolean;
}

/**
 * Input data for creating field mappings
 */
export interface FieldMappingInput {
  /** Source field name */
  source_field: string;

  /** Target field name */
  target_field: string;

  /** Mapping type */
  mapping_type: FieldMappingType;

  /** Optional transformation rule */
  transformation?: string;

  /** Optional validation rules */
  validation_rules?: string;

  /** Optional metadata */
  metadata?: Record<string, string | number | boolean | null>;
}

/**
 * Request to update an existing field mapping
 */
export interface UpdateFieldMappingRequest extends UpdateRequest<Partial<FieldMappingInput>> {
  /** Mapping ID to update */
  mapping_id: string;

  /** Updated mapping data */
  data: Partial<FieldMappingInput>;

  /** Validate after update */
  validate_mapping?: boolean;
}

/**
 * Request to approve a field mapping
 */
export interface ApproveFieldMappingRequest extends BaseApiRequest {
  /** Mapping ID to approve */
  mapping_id: string;

  /** Multi-tenant context */
  context: MultiTenantContext;

  /** Optional approval comment */
  approval_comment?: string;

  /** Auto-progress flow after approval */
  auto_progress?: boolean;
}

/**
 * Request to reject a field mapping
 */
export interface RejectFieldMappingRequest extends BaseApiRequest {
  /** Mapping ID to reject */
  mapping_id: string;

  /** Multi-tenant context */
  context: MultiTenantContext;

  /** Rejection reason */
  rejection_reason: string;

  /** Suggested changes */
  suggested_changes?: string[];
}

/**
 * Bulk operations request for field mappings
 */
export interface BulkFieldMappingRequest extends BaseApiRequest {
  /** Flow ID */
  flow_id: string;

  /** Multi-tenant context */
  context: MultiTenantContext;

  /** Bulk operations to perform */
  operations: FieldMappingOperation[];

  /** Continue on error */
  continue_on_error?: boolean;
}

/**
 * Individual bulk operation
 */
export interface FieldMappingOperation {
  /** Operation type */
  type: 'create' | 'update' | 'delete' | 'approve' | 'reject';

  /** Mapping ID (for update/delete/approve/reject) */
  mapping_id?: string;

  /** Operation data */
  data?: Partial<FieldMappingInput>;

  /** Operation reason */
  reason?: string;
}

// ============================================================================
// FRONTEND-SPECIFIC TYPES (using snake_case to match backend)
// ============================================================================

/**
 * Frontend field mapping interface for UI components
 * Uses snake_case to match backend API response format directly
 */
export interface FieldMapping {
  /** Unique identifier */
  id: string;

  /** Source field name (from CSV/import) */
  source_field: string;

  /** Target field name (system field) */
  target_field: string | null;

  /** Confidence score [0.0-1.0] */
  confidence_score: number;

  /** Mapping type */
  mapping_type: FieldMappingType;

  /** Transformation rule */
  transformation: string | null;

  /** Validation rules */
  validation_rules: string | null;

  /** Mapping status */
  status: FieldMappingStatus;

  /** Sample values from source data */
  sample_values?: unknown[];

  /** AI reasoning for the mapping */
  ai_reasoning?: string;

  /** Whether user-defined */
  is_user_defined?: boolean;

  /** User feedback */
  user_feedback?: string | null;

  /** Validation method used */
  validation_method?: string;

  /** Whether mapping is validated */
  is_validated?: boolean;

  /** Whether this is a placeholder/fallback */
  is_placeholder?: boolean;

  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Frontend field mappings response (using snake_case)
 */
export interface FieldMappingsResult {
  /** Operation success */
  success: boolean;

  /** Flow ID */
  flow_id: string;

  /** Field mappings (snake_case) */
  field_mappings: FieldMapping[];

  /** Total count */
  count: number;

  /** Statistics */
  statistics?: FieldMappingStatistics;

  /** Validation summary */
  validation?: ValidationSummary;
}

/**
 * Field mapping statistics
 */
export interface FieldMappingStatistics {
  /** Total mappings */
  total: number;

  /** Mapped fields */
  mapped: number;

  /** Unmapped fields */
  unmapped: number;

  /** Approved mappings */
  approved: number;

  /** Pending mappings */
  pending: number;

  /** Average confidence */
  average_confidence: number;

  /** Confidence distribution */
  confidence_distribution: {
    high: number;    // >= 0.8
    medium: number;  // 0.5-0.8
    low: number;     // < 0.5
  };
}

/**
 * Validation summary for field mappings
 */
export interface ValidationSummary {
  /** Total validated */
  total_validated: number;

  /** Validation passed */
  passed: number;

  /** Validation failed */
  failed: number;

  /** Warnings */
  warnings: number;

  /** Overall validation score */
  overall_score: number;

  /** Critical issues count */
  critical_issues: number;
}

// ============================================================================
// TYPE GUARDS AND VALIDATION
// ============================================================================

/**
 * Type guard to check if object is a valid FieldMappingItem
 */
export function isFieldMappingItem(obj: unknown): obj is FieldMappingItem {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.source_field === 'string' &&
    (obj.target_field === null || typeof obj.target_field === 'string') &&
    typeof obj.confidence_score === 'number' &&
    obj.confidence_score >= 0 &&
    obj.confidence_score <= 1 &&
    typeof obj.mapping_type === 'string' &&
    (obj.transformation === null || typeof obj.transformation === 'string') &&
    (obj.validation_rules === null || typeof obj.validation_rules === 'string')
  );
}

/**
 * Type guard to check if object is a valid FieldMappingsResponse
 */
export function isFieldMappingsResponse(obj: unknown): obj is FieldMappingsResponse {
  return (
    obj &&
    typeof obj === 'object' &&
    typeof obj.success === 'boolean' &&
    typeof obj.flow_id === 'string' &&
    Array.isArray(obj.field_mappings) &&
    obj.field_mappings.every(isFieldMappingItem) &&
    typeof obj.count === 'number'
  );
}

/**
 * Validates a confidence score value
 */
export function isValidConfidenceScore(score: unknown): score is number {
  return (
    typeof score === 'number' &&
    !isNaN(score) &&
    isFinite(score) &&
    score >= 0 &&
    score <= 1
  );
}

/**
 * Validates a field mapping type
 */
export function isValidMappingType(type: unknown): type is FieldMappingType {
  const validTypes: FieldMappingType[] = ['auto', 'manual', 'suggested', 'direct', 'inferred', 'transformed'];
  return typeof type === 'string' && validTypes.includes(type as FieldMappingType);
}

/**
 * Validates a field mapping status
 */
export function isValidMappingStatus(status: unknown): status is FieldMappingStatus {
  const validStatuses: FieldMappingStatus[] = ['suggested', 'approved', 'rejected', 'pending', 'unmapped'];
  return typeof status === 'string' && validStatuses.includes(status as FieldMappingStatus);
}

// ============================================================================
// TRANSFORMATION UTILITIES
// ============================================================================

/**
 * Transforms backend FieldMappingItem to frontend FieldMapping
 * Both use snake_case fields as per current architecture requirements
 */
export function transformToFrontendMapping(backendItem: FieldMappingItem, id?: string): FieldMapping {
  return {
    id: id || `${backendItem.source_field}_${backendItem.target_field || 'unmapped'}`,
    source_field: backendItem.source_field,
    target_field: backendItem.target_field,
    confidence_score: isValidConfidenceScore(backendItem.confidence_score) ? backendItem.confidence_score : 0.5,
    mapping_type: isValidMappingType(backendItem.mapping_type) ? backendItem.mapping_type : 'auto',
    transformation: backendItem.transformation,
    validation_rules: backendItem.validation_rules,
    status: backendItem.target_field ? 'pending' : 'unmapped',
    sample_values: [],
    ai_reasoning: backendItem.target_field
      ? `AI suggested mapping to ${backendItem.target_field}`
      : 'Field needs mapping assignment',
    is_user_defined: false,
    user_feedback: null,
    validation_method: 'semantic_analysis',
    is_validated: false,
    is_placeholder: !backendItem.target_field
  };
}

/**
 * Transforms frontend FieldMapping to backend FieldMappingItem
 * Both use snake_case fields as per current architecture requirements
 */
export function transformToBackendMapping(frontendMapping: FieldMapping): FieldMappingItem {
  return {
    source_field: frontendMapping.source_field,
    target_field: frontendMapping.target_field,
    confidence_score: frontendMapping.confidence_score,
    mapping_type: frontendMapping.mapping_type,
    transformation: frontendMapping.transformation,
    validation_rules: frontendMapping.validation_rules
  };
}

/**
 * Transforms backend FieldMappingsResponse to frontend FieldMappingsResult
 */
export function transformToFrontendResponse(backendResponse: FieldMappingsResponse): FieldMappingsResult {
  const field_mappings = backendResponse.field_mappings.map((item, index) =>
    transformToFrontendMapping(item, `mapping_${index}`)
  );

  // Calculate statistics
  const statistics: FieldMappingStatistics = {
    total: field_mappings.length,
    mapped: field_mappings.filter(m => m.target_field).length,
    unmapped: field_mappings.filter(m => !m.target_field).length,
    approved: field_mappings.filter(m => m.status === 'approved').length,
    pending: field_mappings.filter(m => m.status === 'pending').length,
    average_confidence: field_mappings.length > 0
      ? field_mappings.reduce((sum, m) => sum + m.confidence_score, 0) / field_mappings.length
      : 0,
    confidence_distribution: {
      high: field_mappings.filter(m => m.confidence_score >= 0.8).length,
      medium: field_mappings.filter(m => m.confidence_score >= 0.5 && m.confidence_score < 0.8).length,
      low: field_mappings.filter(m => m.confidence_score < 0.5).length
    }
  };

  return {
    success: backendResponse.success,
    flow_id: backendResponse.flow_id,
    field_mappings,
    count: backendResponse.count,
    statistics
  };
}
