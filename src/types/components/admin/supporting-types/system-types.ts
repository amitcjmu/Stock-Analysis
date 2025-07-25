/**
 * System Types
 *
 * System configuration, health monitoring, and dependency tracking
 * type definitions.
 */

export interface SystemInfo {
  version: string;
  buildNumber: string;
  environment: Environment;
  uptime: number;
  lastRestart: string;
  configuration: SystemConfiguration;
  health: SystemHealth;
  metrics: SystemMetrics;
  dependencies: SystemDependency[];
}

export interface SystemConfiguration {
  database: DatabaseConfig;
  cache: CacheConfig;
  storage: StorageConfig;
  security: SecurityConfig;
  features: FeatureConfig[];
  limits: SystemLimits;
}

export interface SystemHealth {
  status: HealthStatus;
  checks: HealthCheck[];
  lastCheck: string;
  uptime: number;
  responseTime: number;
}

export interface SystemMetrics {
  requests: RequestMetrics;
  performance: PerformanceMetrics;
  resources: ResourceMetrics;
  errors: ErrorMetrics;
  users: UserMetrics;
}

export interface SystemDependency {
  name: string;
  type: DependencyType;
  version: string;
  status: DependencyStatus;
  lastCheck: string;
  responseTime?: number;
  error?: string;
}

export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  maxConnections: number;
  timeout: number;
  ssl: boolean;
}

export interface CacheConfig {
  provider: 'memory' | 'redis' | 'memcached';
  host?: string;
  port?: number;
  ttl: number;
  maxSize: number;
}

export interface StorageConfig {
  provider: 'local' | 's3' | 'gcs' | 'azure';
  bucket?: string;
  region?: string;
  maxFileSize: number;
  allowedTypes: string[];
}

export interface SecurityConfig {
  encryption: boolean;
  hashing: string;
  tokenExpiry: number;
  maxLoginAttempts: number;
  lockoutDuration: number;
}

export interface FeatureConfig {
  name: string;
  enabled: boolean;
  rollout: number;
  conditions?: Record<string, unknown>;
}

export interface SystemLimits {
  maxUsers: number;
  maxSessions: number;
  maxFileSize: number;
  maxApiCalls: number;
  maxStorage: number;
}

export interface HealthCheck {
  name: string;
  status: HealthStatus;
  responseTime: number;
  lastCheck: string;
  error?: string;
}

export interface RequestMetrics {
  total: number;
  success: number;
  error: number;
  averageResponseTime: number;
  requestsPerSecond: number;
}

export interface PerformanceMetrics {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkIn: number;
  networkOut: number;
}

export interface ResourceMetrics {
  activeConnections: number;
  cacheHitRate: number;
  queueLength: number;
  threadPoolUsage: number;
}

export interface ErrorMetrics {
  total: number;
  rate: number;
  byType: Record<string, number>;
  byEndpoint: Record<string, number>;
}

export interface UserMetrics {
  active: number;
  sessions: number;
  concurrent: number;
  newUsers: number;
  returningUsers: number;
}

// Time and date types
export interface TimeRange {
  start: string;
  end: string;
  preset?: TimeRangePreset;
  timezone?: string;
}

export interface DateRange {
  startDate: string;
  endDate: string;
  includeTime?: boolean;
  timezone?: string;
}

// Export and import types
export interface ExportConfig {
  formats: ExportFormat[];
  filename?: string;
  includeHeaders?: boolean;
  includeMetadata?: boolean;
  compression?: boolean;
  encryption?: boolean;
}

export interface ExportFormat {
  type: ExportType;
  label: string;
  mimeType: string;
  extension: string;
  options?: ExportOptions;
}

export interface ExportOptions {
  sheets?: ExportSheet[];
  columns?: string[];
  filters?: Record<string, unknown>;
  formatting?: ExportFormatting;
  compression?: CompressionOptions;
  encryption?: EncryptionOptions;
}

export interface ExportSheet {
  name: string;
  data: unknown[];
  columns?: TableColumn[];
}

export interface ExportFormatting {
  dateFormat?: string;
  numberFormat?: string;
  currency?: string;
  timezone?: string;
}

export interface CompressionOptions {
  enabled: boolean;
  algorithm: 'gzip' | 'zip' | 'brotli';
  level: number;
}

export interface EncryptionOptions {
  enabled: boolean;
  algorithm: string;
  password?: string;
  keyFile?: string;
}

export interface ImportConfig {
  formats: ImportFormat[];
  validation?: ImportValidation;
  mapping?: ImportMapping;
  processing?: ImportProcessing;
}

export interface ImportFormat {
  type: ImportType;
  label: string;
  mimeTypes: string[];
  extensions: string[];
  maxSize?: number;
}

export interface ImportValidation {
  required: string[];
  schema?: unknown;
  customValidators?: Record<string, (value: unknown) => boolean | string>;
}

export interface ImportMapping {
  sourceFields: string[];
  targetFields: string[];
  mappings: FieldMapping[];
  autoMap?: boolean;
}

export interface FieldMapping {
  source: string;
  target: string;
  transform?: string;
  defaultValue?: unknown;
  required?: boolean;
}

export interface ImportProcessing {
  batchSize?: number;
  skipErrors?: boolean;
  updateExisting?: boolean;
  createMissing?: boolean;
  dryRun?: boolean;
}

// Forward declaration for TableColumn (defined in table-types)
export interface TableColumn {
  key: string;
  title: string;
  dataIndex?: string;
  width?: number | string;
  minWidth?: number;
  maxWidth?: number;
  sortable?: boolean;
  filterable?: boolean;
  searchable?: boolean;
  resizable?: boolean;
  fixed?: 'left' | 'right';
  align?: 'left' | 'center' | 'right';
  render?: (value: unknown, record: unknown, index: number) => React.ReactNode;
  headerRender?: (column: TableColumn) => React.ReactNode;
  filterRender?: (column: TableColumn) => React.ReactNode;
  sorterRender?: (column: TableColumn) => React.ReactNode;
  ellipsis?: boolean;
  copyable?: boolean;
  editable?: boolean;
  required?: boolean;
  validation?: ValidationRule[];
}

// Forward declaration for ValidationRule (defined in form-types)
export interface ValidationRule {
  type: ValidationType;
  value?: unknown;
  message: string;
  validator?: (value: unknown) => boolean | Promise<boolean>;
}

// Enum and union types
export type Environment = 'development' | 'staging' | 'production' | 'test';
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
export type DependencyType = 'database' | 'api' | 'service' | 'storage' | 'cache' | 'queue' | 'external';
export type DependencyStatus = 'available' | 'unavailable' | 'degraded' | 'timeout' | 'error';
export type TimeRangePreset = 'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days' | 'last_90_days' | 'last_year' | 'this_week' | 'this_month' | 'this_year' | 'custom';
export type ExportType = 'csv' | 'excel' | 'pdf' | 'json' | 'xml' | 'txt';
export type ImportType = 'csv' | 'excel' | 'json' | 'xml' | 'txt';
export type ValidationType = 'required' | 'email' | 'url' | 'phone' | 'min' | 'max' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
