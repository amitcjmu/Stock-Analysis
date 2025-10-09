/**
 * Shared Metadata Type Definitions
 *
 * Standardized metadata interfaces to replace Record<string, unknown> patterns
 * across the codebase.
 */

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
