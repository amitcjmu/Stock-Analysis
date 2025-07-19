/**
 * CRUD API Types
 * 
 * Standard CRUD operation request/response patterns.
 */

import { BaseApiRequest, BaseApiResponse, PaginationInfo } from './base-types';
import { MultiTenantContext } from './tenant-types';
import { SortParameter, FilterParameter, SearchParameter, AppliedFilter, AppliedSort, Aggregation } from './query-types';
import { ValidationResult, ValidationError, ValidationWarning } from './validation-types';

// Request/Response patterns
export interface ListRequest extends BaseApiRequest {
  page?: number;
  pageSize?: number;
  sort?: SortParameter[];
  filter?: FilterParameter[];
  search?: SearchParameter;
  fields?: string[];
  include?: string[];
  exclude?: string[];
  context: MultiTenantContext;
}

export interface ListResponse<T> extends BaseApiResponse<T[]> {
  data: T[];
  pagination: PaginationInfo;
  filters?: AppliedFilter[];
  sorting?: AppliedSort[];
  aggregations?: Aggregation[];
}

export interface GetRequest extends BaseApiRequest {
  id: string;
  fields?: string[];
  include?: string[];
  exclude?: string[];
  context: MultiTenantContext;
  version?: string;
  ifModifiedSince?: string;
  ifNoneMatch?: string;
}

export interface GetResponse<T> extends BaseApiResponse<T> {
  data: T;
  version?: string;
  lastModified?: string;
  etag?: string;
}

export interface CreateRequest<T> extends BaseApiRequest {
  data: T;
  context: MultiTenantContext;
  validate?: boolean;
  dryRun?: boolean;
  returnFields?: string[];
}

export interface CreateResponse<T> extends BaseApiResponse<T> {
  data: T;
  validation?: ValidationResult;
  created: boolean;
  location?: string;
}

export interface UpdateRequest<T> extends BaseApiRequest {
  id: string;
  data: Partial<T>;
  context: MultiTenantContext;
  validate?: boolean;
  dryRun?: boolean;
  returnFields?: string[];
  version?: string;
  ifMatch?: string;
}

export interface UpdateResponse<T> extends BaseApiResponse<T> {
  data: T;
  validation?: ValidationResult;
  updated: boolean;
  conflicts?: ConflictInfo[];
}

export interface DeleteRequest extends BaseApiRequest {
  id: string;
  context: MultiTenantContext;
  force?: boolean;
  cascade?: boolean;
  version?: string;
  ifMatch?: string;
}

export interface DeleteResponse extends BaseApiResponse<void> {
  deleted: boolean;
  dependents?: DependentResource[];
  cascade?: CascadeResult[];
}

// Supporting types

export interface ConflictInfo {
  field: string;
  currentValue: any;
  attemptedValue: any;
  resolution: string;
}

export interface DependentResource {
  id: string;
  type: string;
  name: string;
  relationship: string;
}

export interface CascadeResult {
  id: string;
  type: string;
  action: 'deleted' | 'updated' | 'unlinked';
  success: boolean;
  error?: string;
}