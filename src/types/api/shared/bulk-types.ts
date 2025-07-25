/**
 * Bulk Operations API Types
 *
 * Types for bulk operations, batch processing, and bulk responses.
 */

import type { BaseApiRequest, BaseApiResponse, ApiError } from './base-types'
import type { ApiWarning } from './base-types'
import type { MultiTenantContext } from './tenant-types';

export interface BulkRequest<T> extends BaseApiRequest {
  operations: Array<BulkOperation<T>>;
  context: MultiTenantContext;
  continueOnError?: boolean;
  validate?: boolean;
  dryRun?: boolean;
  batchSize?: number;
}

export interface BulkResponse<T> extends BaseApiResponse<Array<BulkResult<T>>> {
  data: Array<BulkResult<T>>;
  summary: BulkSummary;
  partial: boolean;
}

export interface BulkOperation<T> {
  operation: 'create' | 'update' | 'delete' | 'upsert';
  id?: string;
  data?: T;
  version?: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface BulkResult<T> {
  operation: BulkOperation<T>;
  success: boolean;
  data?: T;
  error?: ApiError;
  index: number;
  id?: string;
}

export interface BulkSummary {
  total: number;
  successful: number;
  failed: number;
  skipped: number;
  errors: ApiError[];
  warnings: ApiWarning[];
  processingTime: number;
}
