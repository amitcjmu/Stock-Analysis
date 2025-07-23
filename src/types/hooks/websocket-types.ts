/**
 * WebSocket types for hooks
 * 
 * Common types used for WebSocket communication in hooks.
 */

import type { DynamicValue } from '../api/shared/value-types'
import type { PrimitiveValue } from '../api/shared/value-types'

// WebSocket message data types based on message type
export type WebSocketMessageData = 
  | AnalysisProgressData
  | AnalysisCompleteData
  | AnalysisErrorData
  | ParameterUpdateData
  | AgentActivityData
  | BulkJobUpdateData
  | GenericMessageData;

export interface AnalysisProgressData {
  analysis_id: number;
  step: string;
  progress: number;
  status: 'running' | 'completed' | 'failed';
  message?: string;
  agent_name?: string;
  estimated_time_remaining?: number;
}

export interface AnalysisCompleteData {
  analysis_id: number;
  result: {
    success: boolean;
    summary?: Record<string, PrimitiveValue>;
    artifacts?: string[];
    recommendations?: string[];
  };
}

export interface AnalysisErrorData {
  analysis_id: number;
  error: {
    code: string;
    message: string;
    details?: Record<string, PrimitiveValue>;
  };
}

export interface ParameterUpdateData {
  parameter: string;
  value: PrimitiveValue;
  source?: string;
  timestamp?: string;
}

export interface AgentActivityData {
  agent_name: string;
  activity: string;
  status: 'started' | 'completed' | 'failed';
  metrics?: Record<string, number>;
  output?: DynamicValue;
}

export interface BulkJobUpdateData {
  job_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  completed_applications: number;
  failed_applications: number;
  current_application?: string;
  estimated_time_remaining?: number;
}

export interface GenericMessageData {
  [key: string]: DynamicValue;
}

// WebSocket outgoing message types
export interface WebSocketOutgoingMessage {
  type: string;
  payload: Record<string, PrimitiveValue | PrimitiveValue[]>;
  id?: string;
  timestamp?: string;
}