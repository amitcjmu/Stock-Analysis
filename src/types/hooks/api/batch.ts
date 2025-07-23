/**
 * Batch Operations Hook Types
 * 
 * Hook types for handling multiple API requests in batch,
 * with support for concurrent and sequential execution.
 */

import type { HttpMethod } from './shared';

// Batch Request Hook Types
export interface UseBatchRequestParams {
  requests: BatchRequest[];
  concurrent?: boolean;
  maxConcurrency?: number;
  stopOnError?: boolean;
  retryFailedRequests?: boolean;
  onProgress?: (completed: number, total: number) => void;
  onRequestComplete?: (result: BatchRequestResult, index: number) => void;
  onRequestError?: (error: Error, request: BatchRequest, index: number) => void;
}

export interface UseBatchRequestReturn {
  results: BatchRequestResult[];
  loading: boolean;
  completed: number;
  total: number;
  progress: number;
  errors: BatchError[];
  execute: () => Promise<BatchRequestResult[]>;
  abort: () => void;
  retry: (indices?: number[]) => Promise<BatchRequestResult[]>;
  reset: () => void;
}

// Supporting Types
export interface BatchRequest {
  id?: string;
  url: string;
  method?: HttpMethod;
  data?: unknown;
  headers?: Record<string, string>;
  params?: unknown;
}

export interface BatchRequestResult {
  id?: string;
  success: boolean;
  data?: unknown;
  error?: Error;
  status?: number;
  headers?: Record<string, string>;
}

export interface BatchError {
  index: number;
  request: BatchRequest;
  error: Error;
}