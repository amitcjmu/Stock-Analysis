/**
 * Validation Types
 * 
 * Type definitions for validation errors, warnings, and health issues.
 */

// Validation and Error Types
export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning';
}

export interface ValidationWarning {
  field: string;
  message: string;
  code: string;
  suggestion?: string;
}

export interface HealthIssue {
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  timestamp: string;
  resolved: boolean;
}