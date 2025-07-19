/**
 * Base Discovery Component Types
 * 
 * Core interfaces and base types for discovery components.
 */

import { ReactNode } from 'react';

// Base discovery component types
export interface BaseDiscoveryProps {
  className?: string;
  children?: ReactNode;
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
  metadata?: Record<string, any>;
}

export interface CriticalAttribute {
  id: string;
  name: string;
  description: string;
  dataType: string;
  isRequired: boolean;
  defaultValue?: any;
  validationRules: ValidationRule[];
  mappingStatus: 'mapped' | 'unmapped' | 'partially_mapped';
  sourceFields: string[];
  targetField?: string;
  businessRules?: BusinessRule[];
  priority: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  tags: string[];
  metadata: Record<string, any>;
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
  metadata?: Record<string, any>;
}

export interface ValidationRule {
  type: string;
  parameters: Record<string, any>;
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
  metadata?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning' | 'info';
  value?: any;
  metadata?: Record<string, any>;
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
  value: any;
  logicalOperator?: 'and' | 'or';
}

export interface RuleAction {
  type: string;
  parameters: Record<string, any>;
  description?: string;
}

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';