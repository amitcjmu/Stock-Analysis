/**
 * Flow-related types for hooks
 * 
 * Common types used across flow-related hooks.
 */

import { PrimitiveValue } from '../api/shared/value-types';

// Flow initialization data types
export interface FlowInitializationData {
  flowType: string;
  flowName?: string;
  flowDescription?: string;
  configuration?: Record<string, PrimitiveValue | Record<string, PrimitiveValue>>;
  metadata?: Record<string, PrimitiveValue>;
}

// Phase execution data types  
export interface PhaseExecutionData {
  phaseId?: string;
  phaseName?: string;
  action?: string;
  parameters?: Record<string, PrimitiveValue | Array<PrimitiveValue>>;
  data?: Record<string, PrimitiveValue | Record<string, PrimitiveValue> | Array<PrimitiveValue>>;
  skipValidation?: boolean;
}

// Phase result types
export interface PhaseExecutionResult {
  success: boolean;
  phase?: string;
  status?: string;
  result?: {
    data?: Record<string, PrimitiveValue | Array<PrimitiveValue>>;
    metrics?: Record<string, number>;
    warnings?: string[];
    errors?: string[];
    nextPhase?: string;
    completedSteps?: string[];
  };
  error?: string;
}

// Data transformation types
export interface DataRecord {
  [key: string]: PrimitiveValue | Array<PrimitiveValue> | DataRecord;
}

// Asset and inventory types
export interface AssetProperties {
  id?: string;
  name?: string;
  type?: string;
  status?: string;
  environment?: string;
  location?: string;
  owner?: string;
  criticality?: string;
  dependencies?: string[];
  metadata?: Record<string, PrimitiveValue>;
  customFields?: Record<string, PrimitiveValue>;
}

// Mapping and transformation types
export interface MappingData {
  sourceField: string;
  targetField: string;
  transformation?: string;
  defaultValue?: PrimitiveValue;
  validation?: {
    required?: boolean;
    pattern?: string;
    minLength?: number;
    maxLength?: number;
  };
}

// Error types
export interface FlowError {
  code: string;
  message: string;
  details?: Record<string, PrimitiveValue>;
  timestamp?: string;
  phase?: string;
  recoverable?: boolean;
}