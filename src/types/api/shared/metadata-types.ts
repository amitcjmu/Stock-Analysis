/**
 * Metadata Types
 * 
 * Common metadata structures used across API types.
 */

// Base metadata interface for extensibility
export interface BaseMetadata {
  createdAt?: string;
  updatedAt?: string;
  createdBy?: string;
  updatedBy?: string;
  version?: number;
  tags?: string[];
}

// Session metadata
export interface SessionMetadata extends BaseMetadata {
  ipAddress?: string;
  userAgent?: string;
  location?: string;
  deviceId?: string;
  sessionDuration?: number;
}

// Activity metadata
export interface ActivityMetadata extends BaseMetadata {
  action?: string;
  resource?: string;
  resourceId?: string;
  result?: 'success' | 'failure';
  errorCode?: string;
  errorMessage?: string;
  duration?: number;
}

// Configuration metadata
export interface ConfigurationMetadata extends BaseMetadata {
  environment?: string;
  region?: string;
  instance?: string;
  deploymentId?: string;
  configVersion?: string;
}

// Task/execution metadata
export interface ExecutionMetadata extends BaseMetadata {
  executionId?: string;
  taskName?: string;
  priority?: number;
  retryCount?: number;
  timeout?: number;
  dependencies?: string[];
  parameters?: Record<string, string | number | boolean>;
}

// Agent metadata
export interface AgentMetadata extends BaseMetadata {
  agentId?: string;
  agentName?: string;
  agentType?: string;
  phase?: string;
  status?: string;
  capabilities?: string[];
}

// Flow metadata
export interface FlowMetadata extends BaseMetadata {
  flowId?: string;
  flowType?: string;
  stage?: string;
  progress?: number;
  startTime?: string;
  endTime?: string;
  duration?: number;
}

// Permission metadata
export interface PermissionMetadata extends BaseMetadata {
  grantedBy?: string;
  grantedTo?: string;
  resource?: string;
  scope?: string;
  expiresAt?: string;
  conditions?: Array<{
    field: string;
    operator: string;
    value: string | number | boolean;
  }>;
}

// Generic metadata for flexibility
export type GenericMetadata = BaseMetadata & Record<string, string | number | boolean | string[]>;