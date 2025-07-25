/**
 * Discovery Flow - Validation Types Module
 *
 * Validation rules, business rules, and validation result types.
 * Contains error handling, warnings, and validation configuration.
 *
 * Generated with CC - Code Companion
 */

/**
 * Validation rule definition
 */
export interface ValidationRule {
  type: string;
  parameters: Record<string, string | number | boolean | null>;
  message: string;
}

/**
 * Business rule definition
 */
export interface BusinessRule {
  id: string;
  name: string;
  description: string;
  logic: string;
  priority: number;
}

/**
 * Validation result structure
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  score: number;
  details: Record<string, string | number | boolean | null>;
}

/**
 * Validation error structure
 */
export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning';
}

/**
 * Validation warning structure
 */
export interface ValidationWarning {
  field: string;
  message: string;
  code: string;
  suggestion?: string;
}

/**
 * Validation options for API requests
 */
export interface ValidationOptions {
  strict?: boolean;
  includeWarnings?: boolean;
  validateTransformations?: boolean;
}

/**
 * Import error structure
 */
export interface ImportError {
  row: number;
  column: string;
  message: string;
  severity: 'error' | 'warning';
}

/**
 * Import options configuration
 */
export interface ImportOptions {
  skipValidation?: boolean;
  batchSize?: number;
  delimiter?: string;
  encoding?: string;
}

/**
 * Agent insight structure
 */
export interface AgentInsight {
  agentId: string;
  insight: string;
  confidence: number;
  timestamp: string;
  context: Record<string, string | number | boolean | null>;
}

/**
 * Notification settings for flow configuration
 */
export interface NotificationSettings {
  emailEnabled: boolean;
  slackEnabled: boolean;
  webhookUrl?: string;
}

/**
 * Flow configuration options
 */
export interface FlowConfiguration {
  autoAdvance?: boolean;
  validationLevel?: 'strict' | 'normal' | 'lenient';
  parallelProcessing?: boolean;
  notificationSettings?: NotificationSettings;
}
