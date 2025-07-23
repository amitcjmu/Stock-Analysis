/**
 * Shared Type Definitions for ESLint Compliance Project
 * 
 * This file contains standardized TypeScript interfaces and types to replace
 * 'any' types throughout the codebase. All AI agents should use these shared
 * definitions to ensure consistency and avoid conflicts.
 * 
 * @version 1.0
 * @date 2025-01-21
 * @author CC AI Swarm Project
 */

// =============================================================================
// BASE METADATA SYSTEM
// =============================================================================

/**
 * Base metadata interface for all entities requiring basic tagging and labeling
 */
export interface BaseMetadata {
  /** Key-value tags for categorization */
  tags?: Record<string, string>;
  /** Display labels for UI representation */
  labels?: Record<string, string>;
  /** System annotations for automation */
  annotations?: Record<string, string>;
  /** Custom fields for extensibility */
  customFields?: Record<string, unknown>;
}

/**
 * Extended metadata interface including audit trail information
 */
export interface AuditableMetadata extends BaseMetadata {
  /** Entity creator identifier */
  createdBy?: string;
  /** Last modifier identifier */
  updatedBy?: string;
  /** Entity version for optimistic locking */
  version?: string;
  /** Source system or process that created the entity */
  source?: string;
  /** Creation timestamp */
  createdAt?: string;
  /** Last modification timestamp */
  updatedAt?: string;
}

/**
 * Domain-specific metadata with additional context
 */
export interface DomainMetadata extends AuditableMetadata {
  /** Business domain classification */
  domain?: string;
  /** Compliance and regulatory tags */
  compliance?: Record<string, unknown>;
  /** Security classification level */
  securityLevel?: 'public' | 'internal' | 'confidential' | 'restricted';
  /** Data retention policy references */
  retention?: Record<string, unknown>;
}

// =============================================================================
// ANALYSIS RESULT SYSTEM  
// =============================================================================

/**
 * Base interface for all analysis results across the platform
 */
export interface AnalysisResult {
  /** Type of analysis performed */
  analysisType: string;
  /** Confidence level (0-1) in the analysis results */
  confidence: number;
  /** Generated recommendations based on analysis */
  recommendations: string[];
  /** Analysis-specific data payload */
  data: Record<string, unknown>;
  /** Analysis execution metadata */
  executionMetadata?: {
    startTime: string;
    endTime: string;
    duration: number;
    resourcesUsed?: Record<string, unknown>;
  };
}

/**
 * Financial cost analysis results
 */
export interface CostAnalysis extends AnalysisResult {
  /** Total calculated cost */
  totalCost: number;
  /** Detailed cost breakdown by category */
  breakdown: CostBreakdownItem[];
  /** Currency code (ISO 4217) */
  currency: string;
  /** Cost calculation methodology */
  methodology?: string;
  /** Time period for cost calculation */
  period?: {
    start: string;
    end: string;
    duration: string;
  };
}

/**
 * Individual cost breakdown item
 */
export interface CostBreakdownItem {
  /** Cost category name */
  category: string;
  /** Amount for this category */
  amount: number;
  /** Unit of measurement */
  unit?: string;
  /** Quantity measured */
  quantity?: number;
  /** Unit cost */
  unitCost?: number;
  /** Additional cost details */
  details?: Record<string, unknown>;
}

/**
 * Risk analysis results
 */
export interface RiskAnalysis extends AnalysisResult {
  /** Overall risk score (0-100) */
  riskScore: number;
  /** Risk level classification */
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  /** Identified risk factors */
  riskFactors: RiskFactor[];
  /** Suggested mitigation strategies */
  mitigationStrategies: string[];
}

/**
 * Individual risk factor
 */
export interface RiskFactor {
  /** Risk factor name */
  name: string;
  /** Impact level if risk materializes */
  impact: 'low' | 'medium' | 'high' | 'critical';
  /** Probability of occurrence */
  probability: number;
  /** Risk category */
  category: string;
  /** Detailed description */
  description?: string;
}

// =============================================================================
// CONFIGURATION VALUE SYSTEM
// =============================================================================

/**
 * Union type for common configuration values across the platform
 */
export type ConfigurationValue = 
  | string 
  | number 
  | boolean 
  | string[] 
  | number[]
  | ConfigurationObject;

/**
 * Complex configuration object structure
 */
export interface ConfigurationObject {
  [key: string]: ConfigurationValue | undefined;
}

/**
 * Typed constraint interface for validation and business rules
 */
export interface TypedConstraint {
  /** Constraint type identifier */
  type: string;
  /** Constraint value */
  value: ConfigurationValue;
  /** Human-readable description */
  description: string;
  /** Impact level of constraint violation */
  impact: 'low' | 'medium' | 'high' | 'critical';
  /** Whether constraint is actively enforced */
  enabled?: boolean;
  /** Constraint validation metadata */
  validation?: {
    required: boolean;
    min?: number;
    max?: number;
    pattern?: string;
    allowedValues?: unknown[];
  };
}

/**
 * Configuration criteria for decision-making systems
 */
export interface ConfigurationCriteria {
  /** Criteria identifier */
  id: string;
  /** Criteria name */
  name: string;
  /** Criteria value */
  value: ConfigurationValue;
  /** Weight for multi-criteria decisions */
  weight?: number;
  /** Criteria evaluation operator */
  operator?: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'like';
  /** Reference values for comparison */
  referenceValue?: ConfigurationValue;
}

// =============================================================================
// API RESPONSE SYSTEM
// =============================================================================

/**
 * Standard API response wrapper
 */
export interface ApiResponse<TData = unknown, TError = ApiError> {
  /** Response data payload */
  data: TData;
  /** Error information if request failed */
  error?: TError;
  /** Response metadata */
  meta?: ResponseMetadata;
  /** Response success status */
  success: boolean;
}

/**
 * Standard API error structure  
 */
export interface ApiError {
  /** Error code for programmatic handling */
  code: string;
  /** Human-readable error message */
  message: string;
  /** Additional error details */
  details?: Record<string, unknown>;
  /** Error stack trace (development only) */
  stack?: string;
  /** Correlation ID for tracing */
  correlationId?: string;
}

/**
 * API response metadata
 */
export interface ResponseMetadata {
  /** Request timestamp */
  timestamp: string;
  /** Processing duration in milliseconds */
  duration: number;
  /** API version that processed the request */
  version: string;
  /** Pagination information for list endpoints */
  pagination?: {
    page: number;
    size: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  /** Rate limiting information */
  rateLimit?: {
    limit: number;
    remaining: number;
    resetTime: string;
  };
}

// =============================================================================
// FORM HANDLING SYSTEM
// =============================================================================

/**
 * Generic form field value types
 */
export type FormFieldValue = string | number | boolean | string[] | number[] | FileList | null | undefined;

/**
 * Form field validation result
 */
export interface ValidationResult {
  /** Whether field is valid */
  valid: boolean;
  /** Validation error messages */
  errors: string[];
  /** Validation warnings (non-blocking) */
  warnings?: string[];
}

/**
 * Form field configuration
 */
export interface FormFieldConfig {
  /** Field type for rendering */
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'checkbox' | 'radio' | 'file' | 'textarea';
  /** Whether field is required */
  required?: boolean;
  /** Field placeholder text */
  placeholder?: string;
  /** Field label */
  label?: string;
  /** Field validation rules */
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    custom?: (value: FormFieldValue) => ValidationResult;
  };
  /** Field options for select/radio fields */
  options?: Array<{
    value: string | number;
    label: string;
    disabled?: boolean;
  }>;
}

/**
 * Generic form state interface
 */
export interface FormState<TData extends Record<string, FormFieldValue> = Record<string, FormFieldValue>> {
  /** Form field values */
  values: TData;
  /** Form field errors */
  errors: Partial<Record<keyof TData, string[]>>;
  /** Form submission state */
  isSubmitting: boolean;
  /** Whether form has been touched */
  touched: Partial<Record<keyof TData, boolean>>;
  /** Whether form is valid */
  isValid: boolean;
  /** Form-level error messages */
  formErrors?: string[];
}

// =============================================================================
// COMPONENT PROP SYSTEM
// =============================================================================

/**
 * Base component props shared across all components
 */
export interface BaseComponentProps {
  /** Component CSS class name */
  className?: string;
  /** Component inline styles */
  style?: React.CSSProperties;
  /** Component test identifier */
  'data-testid'?: string;
  /** Component accessibility ID */
  id?: string;
  /** Component aria label */
  'aria-label'?: string;
}

/**
 * Data-driven component props
 */
export interface DataComponentProps<TData = unknown> extends BaseComponentProps {
  /** Data to display/manipulate */
  data: TData;
  /** Loading state */
  loading?: boolean;
  /** Error state */
  error?: string | null;
  /** Data refresh handler */
  onRefresh?: () => void;
}

/**
 * Interactive component event handlers
 */
export interface ComponentEventHandlers<TData = unknown, TEvent = React.SyntheticEvent> {
  /** Selection change handler */
  onSelect?: (item: TData, event: TEvent) => void;
  /** Item action handler */
  onAction?: (action: string, item: TData, event: TEvent) => void;
  /** Change handler */
  onChange?: (value: TData, event: TEvent) => void;
  /** Focus handler */
  onFocus?: (event: TEvent) => void;
  /** Blur handler */
  onBlur?: (event: TEvent) => void;
}

/**
 * Component configuration options
 */
export interface ComponentConfig {
  /** Visual theme */
  theme?: 'light' | 'dark' | 'auto';
  /** Component size variant */
  size?: 'small' | 'medium' | 'large';
  /** Disabled state */
  disabled?: boolean;
  /** Read-only state */
  readonly?: boolean;
  /** Density mode for data display */
  density?: 'compact' | 'normal' | 'comfortable';
}

// =============================================================================
// REACT HOOK SYSTEM
// =============================================================================

/**
 * Standard hook state pattern
 */
export interface HookState<TData = unknown> {
  /** Hook data */
  data: TData;
  /** Loading state */
  loading: boolean;
  /** Error state */
  error: string | null;
  /** Whether initial load has completed */
  initialized: boolean;
}

/**
 * Hook action handlers
 */
export interface HookActions<TData = unknown> {
  /** Update data */
  update: (data: Partial<TData>) => void;
  /** Reset to initial state */
  reset: () => void;
  /** Refresh/reload data */
  refresh: () => Promise<void>;
  /** Set loading state */
  setLoading: (loading: boolean) => void;
  /** Set error state */
  setError: (error: string | null) => void;
}

/**
 * Hook configuration options
 */
export interface HookConfig {
  /** Whether to automatically initialize */
  autoInit?: boolean;
  /** Initial data value */
  initialData?: unknown;
  /** Error retry configuration */
  retry?: {
    attempts: number;
    delay: number;
    backoff?: number;
  };
  /** Caching configuration */
  cache?: {
    enabled: boolean;
    ttl: number;
    key: string;
  };
}

// =============================================================================
// UTILITY TYPES
// =============================================================================

/**
 * Deep partial type for nested object updates
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

/**
 * Make specific properties required
 */
export type RequireFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

/**
 * Extract array element type
 */
export type ArrayElement<T> = T extends Array<infer U> ? U : never;

/**
 * Function type constraints
 */
export type AsyncFunction<TArgs extends unknown[] = unknown[], TReturn = unknown> = 
  (...args: TArgs) => Promise<TReturn>;

export type SyncFunction<TArgs extends unknown[] = unknown[], TReturn = unknown> = 
  (...args: TArgs) => TReturn;

/**
 * ID types for different domains
 */
export type EntityId = string;
export type UserId = string;
export type SessionId = string;
export type CorrelationId = string;

// =============================================================================
// TYPE GUARDS AND VALIDATION
// =============================================================================

/**
 * Type guard function signature
 */
export type TypeGuard<T> = (value: unknown) => value is T;

/**
 * Validation function signature
 */
export type ValidationFunction<T> = (value: T) => ValidationResult;

/**
 * Schema validation result
 */
export interface SchemaValidationResult {
  /** Whether validation passed */
  valid: boolean;
  /** Validation errors by field path */
  errors: Record<string, string[]>;
  /** Validated and transformed data */
  data?: unknown;
}

// =============================================================================
// EXPORT COLLECTIONS
// =============================================================================

/**
 * All metadata types
 */
export type MetadataTypes = BaseMetadata | AuditableMetadata | DomainMetadata;

/**
 * All analysis types
 */
export type AnalysisTypes = AnalysisResult | CostAnalysis | RiskAnalysis;

/**
 * All configuration types  
 */
export type ConfigurationTypes = ConfigurationValue | TypedConstraint | ConfigurationCriteria;

/**
 * All API types
 */
export type ApiTypes = ApiResponse | ApiError | ResponseMetadata;

/**
 * All component types
 */
export type ComponentTypes = BaseComponentProps | DataComponentProps | ComponentEventHandlers | ComponentConfig;

/**
 * All hook types
 */
export type HookTypes = HookState | HookActions | HookConfig;