/**
 * Base API Types
 * 
 * Core API interfaces for requests, responses, errors, and metadata.
 */

// Base request/response types
export interface BaseApiRequest {
  requestId?: string;
  timestamp?: string;
  version?: string;
  metadata?: Record<string, any>;
}

export interface BaseApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: ApiError;
  errors?: ApiError[];
  warnings?: ApiWarning[];
  metadata: ResponseMetadata;
  pagination?: PaginationInfo;
  links?: ApiLinks;
}

export interface ApiError {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, any>;
  stack?: string;
  timestamp: string;
  requestId?: string;
  correlation?: string;
}

export interface ApiWarning {
  code: string;
  message: string;
  field?: string;
  details?: Record<string, any>;
  severity: 'low' | 'medium' | 'high';
}

export interface ResponseMetadata {
  requestId: string;
  timestamp: string;
  version: string;
  processingTime: number;
  serverTime: string;
  rateLimit?: RateLimitInfo;
  cacheInfo?: CacheInfo;
  deprecation?: DeprecationInfo;
}

export interface PaginationInfo {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
  offset: number;
  limit: number;
}

export interface ApiLinks {
  self?: string;
  first?: string;
  last?: string;
  next?: string;
  previous?: string;
  related?: Record<string, string>;
}

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  reset: number;
  resetTime: string;
  retryAfter?: number;
  burst?: number;
  window: number;
}

export interface CacheInfo {
  cached: boolean;
  cacheKey?: string;
  maxAge?: number;
  age?: number;
  expires?: string;
  lastModified?: string;
  etag?: string;
}

export interface DeprecationInfo {
  deprecated: boolean;
  deprecationDate?: string;
  sunsetDate?: string;
  replacementUrl?: string;
  documentation?: string;
  message?: string;
}