/**
 * Base Discovery Component Types
 * 
 * Core interfaces and base types for discovery components.
 */

import type { ReactNode, HTMLAttributes } from 'react';

// Base discovery component types
export interface BaseDiscoveryProps extends Omit<HTMLAttributes<HTMLDivElement>, 'className'> {
  className?: string;
  children?: ReactNode;
  testId?: string;
  'data-testid'?: string;
}

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
  metadata?: Record<string, string | number | boolean | null>;
}

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
  metadata?: Record<string, string | number | boolean | null>;
}

export interface ValidationRule {
  type: string;
  parameters: Record<string, string | number | boolean | null>;
  message: string;
  severity?: 'error' | 'warning' | 'info';
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

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning' | 'info';
  value?: unknown;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface ImportError {
  row: number;
  column: string;
  message: string;
  severity: 'error' | 'warning';
  code?: string;
  suggestion?: string;
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

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';