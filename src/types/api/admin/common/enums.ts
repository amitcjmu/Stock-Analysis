/**
 * Common Enums
 *
 * Shared enumeration types used across admin modules for
 * priorities, severities, statuses, and other common concepts.
 *
 * Generated with CC for modular admin type organization.
 */

/**
 * Priority levels - used for notifications, recommendations, etc.
 */
export type Priority = 'low' | 'medium' | 'high' | 'critical';

/**
 * Extended priority with normal and urgent
 */
export type ExtendedPriority = 'low' | 'normal' | 'high' | 'urgent' | 'critical';

/**
 * Severity levels - used for audit logs, security events, etc.
 */
export type Severity = 'low' | 'medium' | 'high' | 'critical';

/**
 * Extended severity with info
 */
export type ExtendedSeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

/**
 * Generic status types
 */
export type Status = 'active' | 'inactive' | 'pending' | 'suspended' | 'archived';

/**
 * Outcome types for operations
 */
export type Outcome = 'success' | 'failure' | 'partial' | 'blocked' | 'error';

/**
 * Change types for tracking modifications
 */
export type ChangeType = 'create' | 'update' | 'delete' | 'restore' | 'encrypt' | 'decrypt';

/**
 * Confidence levels for analytics and predictions
 */
export type ConfidenceLevel = 'very_low' | 'low' | 'medium' | 'high' | 'very_high';

/**
 * Trend directions
 */
export type TrendDirection = 'increasing' | 'decreasing' | 'stable' | 'volatile' | 'seasonal';

/**
 * Impact levels
 */
export type ImpactLevel = 'none' | 'low' | 'medium' | 'high' | 'critical';

/**
 * Business impact levels
 */
export type BusinessImpact = 'none' | 'minimal' | 'moderate' | 'significant' | 'severe';

/**
 * Technical impact levels
 */
export type TechnicalImpact = 'none' | 'minimal' | 'moderate' | 'significant' | 'severe';

/**
 * Data sensitivity levels
 */
export type DataSensitivity = 'public' | 'internal' | 'confidential' | 'restricted';

/**
 * Environment types
 */
export type Environment = 'production' | 'staging' | 'development' | 'testing' | 'sandbox';

/**
 * Authentication methods
 */
export type AuthenticationMethod =
  | 'password'
  | 'mfa'
  | 'sso'
  | 'api_key'
  | 'oauth'
  | 'certificate'
  | 'biometric';

/**
 * Session types
 */
export type SessionType = 'interactive' | 'api' | 'service' | 'scheduled' | 'system';

/**
 * Complexity levels
 */
export type ComplexityLevel = 'simple' | 'moderate' | 'complex' | 'very_complex';

/**
 * Effort levels
 */
export type EffortLevel = 'minimal' | 'low' | 'medium' | 'high' | 'very_high';

/**
 * Effectiveness levels
 */
export type EffectivenessLevel = 'ineffective' | 'partially_effective' | 'effective' | 'highly_effective';

/**
 * Resource types
 */
export type ResourceType = 'documentation' | 'tool' | 'service' | 'training' | 'template';

/**
 * Condition operators for filtering
 */
export type ConditionOperator =
  | 'equals'
  | 'not_equals'
  | 'contains'
  | 'not_contains'
  | 'greater_than'
  | 'less_than'
  | 'in'
  | 'not_in'
  | 'exists'
  | 'not_exists'
  | 'matches'
  | 'starts_with'
  | 'ends_with';

/**
 * Filter operators for queries
 */
export type FilterOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'greater_equal'
  | 'less_equal'
  | 'contains'
  | 'not_contains'
  | 'starts_with'
  | 'ends_with'
  | 'in'
  | 'not_in'
  | 'between';
