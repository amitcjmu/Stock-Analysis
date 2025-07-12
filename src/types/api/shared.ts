/**
 * Shared API Types
 * 
 * Common API interfaces, patterns, and utilities used across all API endpoints.
 * Provides consistent request/response structures and error handling.
 */

// Base API types
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

// Multi-tenant context
export interface MultiTenantContext {
  clientAccountId: string;
  engagementId: string;
  userId: string;
  tenantId?: string;
  organizationId?: string;
  workspaceId?: string;
  permissions?: string[];
  roles?: string[];
  scope?: string[];
}

export interface TenantHeaders {
  'X-Client-Account-ID': string;
  'X-Engagement-ID': string;
  'X-User-ID': string;
  'X-Tenant-ID'?: string;
  'X-Organization-ID'?: string;
  'X-Workspace-ID'?: string;
  'X-Request-ID'?: string;
  'X-Correlation-ID'?: string;
  'X-Session-ID'?: string;
  'X-Device-ID'?: string;
  'X-User-Agent'?: string;
  'X-Source'?: string;
  'X-Version'?: string;
}

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

// File upload/download
export interface FileUploadRequest extends BaseApiRequest {
  file: File | Blob;
  fileName?: string;
  contentType?: string;
  context: MultiTenantContext;
  metadata?: Record<string, any>;
  tags?: string[];
  encryption?: EncryptionOptions;
  virusScan?: boolean;
  overwrite?: boolean;
}

export interface FileUploadResponse extends BaseApiResponse<FileInfo> {
  data: FileInfo;
  uploaded: boolean;
  location: string;
  virusScanResult?: VirusScanResult;
}

export interface FileDownloadRequest extends BaseApiRequest {
  fileId: string;
  context: MultiTenantContext;
  version?: string;
  format?: string;
  transformation?: TransformationOptions;
  includeMetadata?: boolean;
}

export interface FileDownloadResponse {
  file: Blob;
  fileName: string;
  contentType: string;
  size: number;
  lastModified: string;
  etag: string;
  metadata?: FileMetadata;
}

// Search and filtering
export interface SearchRequest extends BaseApiRequest {
  query: string;
  type?: string[];
  filters?: FilterParameter[];
  sort?: SortParameter[];
  page?: number;
  pageSize?: number;
  highlight?: boolean;
  facets?: string[];
  boost?: BoostParameter[];
  context: MultiTenantContext;
}

export interface SearchResponse<T> extends BaseApiResponse<SearchResult<T>[]> {
  data: SearchResult<T>[];
  query: string;
  took: number;
  totalHits: number;
  maxScore: number;
  facets?: SearchFacet[];
  suggestions?: SearchSuggestion[];
  pagination: PaginationInfo;
}

export interface AdvancedSearchRequest extends BaseApiRequest {
  criteria: SearchCriteria;
  aggregations?: AggregationRequest[];
  highlight?: HighlightOptions;
  sort?: SortParameter[];
  page?: number;
  pageSize?: number;
  context: MultiTenantContext;
}

export interface AdvancedSearchResponse<T> extends BaseApiResponse<SearchResult<T>[]> {
  data: SearchResult<T>[];
  aggregations?: AggregationResult[];
  suggestions?: SearchSuggestion[];
  statistics: SearchStatistics;
  pagination: PaginationInfo;
}

// Export/Import
export interface ExportRequest extends BaseApiRequest {
  format: ExportFormat;
  data?: ExportDataSpec;
  filters?: FilterParameter[];
  fields?: string[];
  context: MultiTenantContext;
  compression?: CompressionOptions;
  encryption?: EncryptionOptions;
  schedule?: ScheduleOptions;
}

export interface ExportResponse extends BaseApiResponse<ExportResult> {
  data: ExportResult;
  exportId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
  expiresAt?: string;
}

export interface ImportRequest extends BaseApiRequest {
  file: File;
  format: ImportFormat;
  options?: ImportOptions;
  mapping?: FieldMapping[];
  validation?: ValidationOptions;
  context: MultiTenantContext;
  dryRun?: boolean;
}

export interface ImportResponse extends BaseApiResponse<ImportResult> {
  data: ImportResult;
  importId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  validation?: ValidationResult;
  preview?: ImportPreview;
}

// Real-time updates
export interface WebSocketMessage<T = any> {
  id: string;
  type: string;
  event: string;
  data: T;
  timestamp: string;
  context: MultiTenantContext;
  correlation?: string;
  retry?: number;
}

export interface SubscriptionRequest extends BaseApiRequest {
  events: string[];
  filters?: FilterParameter[];
  context: MultiTenantContext;
  heartbeat?: number;
  compression?: boolean;
}

export interface SubscriptionResponse extends BaseApiResponse<SubscriptionInfo> {
  data: SubscriptionInfo;
  subscriptionId: string;
  websocketUrl: string;
  events: string[];
  expiresAt: string;
}

// Health and monitoring
export interface HealthCheckRequest extends BaseApiRequest {
  deep?: boolean;
  services?: string[];
  timeout?: number;
}

export interface HealthCheckResponse extends BaseApiResponse<HealthStatus> {
  data: HealthStatus;
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: HealthCheck[];
  timestamp: string;
  uptime: number;
  version: string;
}

export interface MetricsRequest extends BaseApiRequest {
  metrics?: string[];
  timeRange?: TimeRange;
  granularity?: string;
  aggregation?: string[];
  filters?: FilterParameter[];
  context?: MultiTenantContext;
}

export interface MetricsResponse extends BaseApiResponse<MetricValue[]> {
  data: MetricValue[];
  timeRange: TimeRange;
  granularity: string;
  totalDataPoints: number;
}

// Supporting types
export interface SortParameter {
  field: string;
  direction: 'asc' | 'desc';
  priority?: number;
  nullsFirst?: boolean;
}

export interface FilterParameter {
  field: string;
  operator: FilterOperator;
  value: any;
  values?: any[];
  caseSensitive?: boolean;
  negate?: boolean;
}

export interface SearchParameter {
  query: string;
  fields?: string[];
  operator?: 'and' | 'or';
  boost?: Record<string, number>;
  fuzzy?: boolean;
  exactMatch?: boolean;
  caseSensitive?: boolean;
}

export interface AppliedFilter {
  field: string;
  operator: FilterOperator;
  value: any;
  label?: string;
  count?: number;
}

export interface AppliedSort {
  field: string;
  direction: 'asc' | 'desc';
  label?: string;
}

export interface Aggregation {
  name: string;
  type: string;
  field: string;
  buckets?: AggregationBucket[];
  value?: number;
  metrics?: Record<string, number>;
}

export interface AggregationBucket {
  key: any;
  label?: string;
  count: number;
  selected?: boolean;
  metrics?: Record<string, number>;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  score?: number;
  summary?: string;
  details?: Record<string, any>;
}

export interface ValidationError {
  field: string;
  code: string;
  message: string;
  value?: any;
  constraint?: any;
  path?: string;
}

export interface ValidationWarning {
  field: string;
  code: string;
  message: string;
  value?: any;
  suggestion?: string;
  path?: string;
}

export interface ConflictInfo {
  field: string;
  clientValue: any;
  serverValue: any;
  lastModified: string;
  version: string;
}

export interface DependentResource {
  type: string;
  id: string;
  name?: string;
  relationship: string;
  blocked: boolean;
}

export interface CascadeResult {
  type: string;
  id: string;
  action: 'deleted' | 'updated' | 'skipped';
  success: boolean;
  error?: string;
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

export interface FileInfo {
  id: string;
  name: string;
  originalName: string;
  size: number;
  mimeType: string;
  extension: string;
  hash: string;
  url: string;
  downloadUrl: string;
  thumbnail?: string;
  metadata: FileMetadata;
  uploadedAt: string;
  uploadedBy: string;
  virusScanResult?: VirusScanResult;
}

export interface FileMetadata {
  width?: number;
  height?: number;
  duration?: number;
  pages?: number;
  encoding?: string;
  colorSpace?: string;
  compression?: string;
  custom?: Record<string, any>;
}

export interface VirusScanResult {
  scanned: boolean;
  clean: boolean;
  threats?: ThreatInfo[];
  scanEngine: string;
  scanTime: string;
  signature: string;
}

export interface ThreatInfo {
  name: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description?: string;
}

export interface EncryptionOptions {
  enabled: boolean;
  algorithm?: string;
  keyId?: string;
  clientEncrypted?: boolean;
}

export interface TransformationOptions {
  resize?: { width?: number; height?: number; quality?: number };
  crop?: { x: number; y: number; width: number; height: number };
  rotate?: number;
  format?: string;
  quality?: number;
  watermark?: WatermarkOptions;
}

export interface WatermarkOptions {
  text?: string;
  image?: string;
  position: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';
  opacity: number;
  size: number;
}

export interface SearchResult<T> {
  item: T;
  score: number;
  highlights?: Record<string, string[]>;
  explanation?: SearchExplanation;
  type: string;
  id: string;
}

export interface SearchFacet {
  field: string;
  name: string;
  type: 'terms' | 'range' | 'date' | 'numeric';
  buckets: FacetBucket[];
  missing?: number;
  other?: number;
}

export interface FacetBucket {
  key: any;
  label?: string;
  count: number;
  selected?: boolean;
  from?: any;
  to?: any;
}

export interface SearchSuggestion {
  type: 'term' | 'phrase' | 'completion';
  text: string;
  score: number;
  highlighted?: string;
  category?: string;
}

export interface SearchCriteria {
  query?: string;
  filters: FilterCriteria[];
  must?: SearchCriteria[];
  should?: SearchCriteria[];
  mustNot?: SearchCriteria[];
  boost?: number;
  minimumShouldMatch?: number | string;
}

export interface FilterCriteria {
  field: string;
  operator: FilterOperator;
  value: any;
  values?: any[];
  boost?: number;
  caseSensitive?: boolean;
}

export interface AggregationRequest {
  name: string;
  type: 'terms' | 'range' | 'date_histogram' | 'histogram' | 'stats' | 'cardinality';
  field: string;
  size?: number;
  order?: { field: string; direction: 'asc' | 'desc' };
  ranges?: AggregationRange[];
  interval?: string;
  minDocCount?: number;
  missing?: any;
}

export interface AggregationRange {
  from?: any;
  to?: any;
  key?: string;
  label?: string;
}

export interface AggregationResult {
  name: string;
  type: string;
  buckets?: AggregationResultBucket[];
  value?: number;
  values?: Record<string, number>;
  docCountErrorUpperBound?: number;
  sumOtherDocCount?: number;
}

export interface AggregationResultBucket {
  key: any;
  keyAsString?: string;
  docCount: number;
  from?: any;
  to?: any;
  subAggregations?: Record<string, AggregationResult>;
}

export interface HighlightOptions {
  fields: string[];
  fragmentSize?: number;
  numberOfFragments?: number;
  preTags?: string[];
  postTags?: string[];
  requireFieldMatch?: boolean;
}

export interface SearchStatistics {
  totalHits: number;
  maxScore: number;
  took: number;
  timedOut: boolean;
  shards: ShardInfo;
}

export interface ShardInfo {
  total: number;
  successful: number;
  skipped: number;
  failed: number;
}

export interface SearchExplanation {
  value: number;
  description: string;
  details?: SearchExplanation[];
}

export interface ExportDataSpec {
  type: 'query' | 'ids' | 'all';
  query?: any;
  ids?: string[];
  fields?: string[];
  relations?: string[];
}

export interface ExportResult {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  format: ExportFormat;
  downloadUrl?: string;
  size?: number;
  recordCount?: number;
  error?: string;
  createdAt: string;
  completedAt?: string;
  expiresAt?: string;
}

export interface ImportResult {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  recordsTotal: number;
  recordsProcessed: number;
  recordsSuccessful: number;
  recordsFailed: number;
  errors?: ImportError[];
  warnings?: ImportWarning[];
  createdAt: string;
  completedAt?: string;
}

export interface ImportPreview {
  headers: string[];
  sample: any[][];
  totalRows: number;
  detectedFormat: ImportFormat;
  encoding: string;
  delimiter?: string;
  quoteChar?: string;
  escapeChar?: string;
}

export interface ImportError {
  row: number;
  column?: string;
  field?: string;
  code: string;
  message: string;
  value?: any;
}

export interface ImportWarning {
  row?: number;
  column?: string;
  field?: string;
  code: string;
  message: string;
  value?: any;
  suggestion?: string;
}

export interface SubscriptionInfo {
  id: string;
  events: string[];
  filters: FilterParameter[];
  status: 'active' | 'paused' | 'expired' | 'error';
  createdAt: string;
  expiresAt: string;
  lastHeartbeat?: string;
  messageCount: number;
  errorCount: number;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  uptime: number;
  timestamp: string;
  environment: string;
  region?: string;
  checks: HealthCheck[];
  dependencies: DependencyHealth[];
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  message?: string;
  time: string;
  duration: number;
  details?: Record<string, any>;
}

export interface DependencyHealth {
  name: string;
  type: 'database' | 'cache' | 'queue' | 'external_api' | 'storage' | 'other';
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime?: number;
  lastChecked: string;
  error?: string;
  version?: string;
}

export interface MetricValue {
  name: string;
  value: number;
  unit?: string;
  timestamp: string;
  tags?: Record<string, string>;
  aggregation?: string;
}

export interface TimeRange {
  start: string;
  end: string;
  duration?: number;
  preset?: string;
}

export interface CompressionOptions {
  enabled: boolean;
  algorithm?: 'gzip' | 'brotli' | 'deflate';
  level?: number;
}

export interface ScheduleOptions {
  immediate?: boolean;
  delay?: number;
  schedule?: string; // cron expression
  timezone?: string;
  retries?: number;
  retryDelay?: number;
}

export interface BoostParameter {
  field: string;
  boost: number;
  condition?: FilterParameter;
}

export interface FieldMapping {
  source: string;
  target: string;
  transformation?: string;
  defaultValue?: any;
  required?: boolean;
  validation?: ValidationRule[];
}

export interface ValidationRule {
  type: string;
  parameters?: Record<string, any>;
  message?: string;
}

export interface ValidationOptions {
  strict?: boolean;
  skipInvalid?: boolean;
  maxErrors?: number;
  validateSchema?: boolean;
  customRules?: ValidationRule[];
}

export interface ImportOptions {
  delimiter?: string;
  quoteChar?: string;
  escapeChar?: string;
  encoding?: string;
  hasHeader?: boolean;
  skipRows?: number;
  maxRows?: number;
  batchSize?: number;
  upsert?: boolean;
  onConflict?: 'skip' | 'update' | 'error';
  dateFormat?: string;
  numberFormat?: string;
  booleanFormat?: Record<string, boolean>;
  nullValues?: string[];
  trimWhitespace?: boolean;
  emptyStringAsNull?: boolean;
}

// Enum-like types
export type FilterOperator = 
  | 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte'
  | 'in' | 'not_in' | 'contains' | 'not_contains'
  | 'starts_with' | 'ends_with' | 'regex' | 'not_regex'
  | 'exists' | 'not_exists' | 'is_null' | 'is_not_null'
  | 'between' | 'not_between' | 'within' | 'intersects';

export type ExportFormat = 
  | 'csv' | 'tsv' | 'json' | 'jsonl' | 'xml' | 'xlsx' | 'parquet' | 'avro';

export type ImportFormat = 
  | 'csv' | 'tsv' | 'json' | 'jsonl' | 'xml' | 'xlsx' | 'yaml' | 'toml';

// HTTP status code helpers
export interface HttpStatus {
  code: number;
  message: string;
  category: 'informational' | 'success' | 'redirection' | 'client_error' | 'server_error';
}

export const HTTP_STATUS: Record<number, HttpStatus> = {
  200: { code: 200, message: 'OK', category: 'success' },
  201: { code: 201, message: 'Created', category: 'success' },
  202: { code: 202, message: 'Accepted', category: 'success' },
  204: { code: 204, message: 'No Content', category: 'success' },
  400: { code: 400, message: 'Bad Request', category: 'client_error' },
  401: { code: 401, message: 'Unauthorized', category: 'client_error' },
  403: { code: 403, message: 'Forbidden', category: 'client_error' },
  404: { code: 404, message: 'Not Found', category: 'client_error' },
  409: { code: 409, message: 'Conflict', category: 'client_error' },
  422: { code: 422, message: 'Unprocessable Entity', category: 'client_error' },
  429: { code: 429, message: 'Too Many Requests', category: 'client_error' },
  500: { code: 500, message: 'Internal Server Error', category: 'server_error' },
  502: { code: 502, message: 'Bad Gateway', category: 'server_error' },
  503: { code: 503, message: 'Service Unavailable', category: 'server_error' },
  504: { code: 504, message: 'Gateway Timeout', category: 'server_error' },
};

// API client configuration
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
  headers?: Record<string, string>;
  auth?: ApiAuthConfig;
  interceptors?: ApiInterceptors;
  cache?: ApiCacheConfig;
  logging?: ApiLoggingConfig;
}

export interface ApiAuthConfig {
  type: 'none' | 'bearer' | 'basic' | 'apikey' | 'oauth2';
  token?: string;
  username?: string;
  password?: string;
  apiKey?: string;
  oauth2?: OAuth2Config;
}

export interface OAuth2Config {
  clientId: string;
  clientSecret?: string;
  scope?: string[];
  tokenUrl: string;
  refreshUrl?: string;
  revokeUrl?: string;
}

export interface ApiInterceptors {
  request?: RequestInterceptor[];
  response?: ResponseInterceptor[];
}

export interface RequestInterceptor {
  name: string;
  handler: (config: any) => any | Promise<any>;
  errorHandler?: (error: any) => any | Promise<any>;
}

export interface ResponseInterceptor {
  name: string;
  handler: (response: any) => any | Promise<any>;
  errorHandler?: (error: any) => any | Promise<any>;
}

export interface ApiCacheConfig {
  enabled: boolean;
  defaultTTL?: number;
  maxSize?: number;
  storage?: 'memory' | 'localStorage' | 'sessionStorage' | 'indexedDB';
  keyPrefix?: string;
  exclude?: string[];
}

export interface ApiLoggingConfig {
  enabled: boolean;
  level?: 'debug' | 'info' | 'warn' | 'error';
  logRequests?: boolean;
  logResponses?: boolean;
  logErrors?: boolean;
  sensitiveFields?: string[];
  maxBodySize?: number;
}