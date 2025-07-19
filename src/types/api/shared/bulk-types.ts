/**
 * Bulk Operations API Types
 * 
 * Types for bulk operations, batch processing, and bulk responses.
 */

import { BaseApiRequest, BaseApiResponse, ApiError, ApiWarning } from './base-types';
import { MultiTenantContext } from './tenant-types';

export interface BulkRequest<T> extends BaseApiRequest {
  operations: BulkOperation<T>[];
  context: MultiTenantContext;
  continueOnError?: boolean;
  validate?: boolean;
  dryRun?: boolean;
  batchSize?: number;
}

export interface BulkResponse<T> extends BaseApiResponse<BulkResult<T>[]> {
  data: BulkResult<T>[];
  summary: BulkSummary;
  partial: boolean;
}

export interface BulkOperation<T> {
  operation: 'create' | 'update' | 'delete' | 'upsert';
  id?: string;
  data?: T;
  version?: string;
  metadata?: Record<string, any>;
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