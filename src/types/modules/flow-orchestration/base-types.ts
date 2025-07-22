/**
 * Flow Orchestration Base Types
 * 
 * Common types and base interfaces used across the flow orchestration system.
 */

// Base agent configuration types
export interface AgentConfiguration {
  id: string;
  name: string;
  role: string;
  goal: string;
  backstory: string;
  capabilities: string[];
  tools: string[];
  llmConfig: LLMConfiguration;
  memoryEnabled: boolean;
  verboseLogging: boolean;
}

export interface LLMConfiguration {
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  frequencyPenalty: number;
  presencePenalty: number;
}

export interface FlowExecutionContext {
  flowId: string;
  flowType: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  executionId: string;
  startTime: string;
  parameters: Record<string, string | number | boolean | null>;
  metadata: Record<string, string | number | boolean | null>;
}

// Time range and metric types
export interface TimeRange {
  start: string;
  end: string;
}

export interface MetricSample {
  timestamp: string;
  value: number;
  metadata?: Record<string, string | number | boolean | null>;
}

// Common error and validation types
export interface ExecutionError {
  code: string;
  message: string;
  details?: Record<string, string | number | boolean | null>;
  timestamp: string;
  source?: string;
  stack?: string;
}

export interface ExecutionWarning {
  code: string;
  message: string;
  details?: Record<string, string | number | boolean | null>;
  timestamp: string;
  source?: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  details?: Record<string, string | number | boolean | null>;
}

export interface BackupResult {
  backupId: string;
  flowId: string;
  timestamp: string;
  size: number;
  checksum: string;
  location: string;
}

export interface DeletionResult {
  flowId: string;
  deletedChildFlows: string[];
  deletedResources: string[];
  errors: string[];
  success: boolean;
}

// Common filter types
export interface FlowFilters {
  status?: string[];
  flowType?: string[];
  clientAccountId?: string;
  engagementId?: string;
  userId?: string;
  dateRange?: TimeRange;
  priority?: string[];
}

export interface EventFilters {
  eventTypes?: string[];
  severity?: string[];
  source?: string[];
  dateRange?: TimeRange;
  category?: string[];
}

export interface AlertFilters {
  severity?: string[];
  status?: string[];
  dateRange?: TimeRange;
  category?: string[];
}

// Policy and configuration types
export interface RetryPolicy {
  maxAttempts: number;
  backoffStrategy: 'linear' | 'exponential' | 'fixed';
  initialDelay: number;
  maxDelay: number;
  retryConditions: string[];
}

export interface ExecutionConstraints {
  maxDuration: number;
  maxMemory: number;
  maxCpuUsage: number;
  allowedResources: string[];
  restrictions: Record<string, string | number | boolean | null>;
}