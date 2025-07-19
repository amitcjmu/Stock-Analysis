/**
 * Admin Supporting Types
 * 
 * Common type definitions and supporting interfaces used across admin components.
 * This module contains shared types that are used by multiple admin component modules.
 */

import { ReactNode } from 'react';

// Base user and role types
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  avatar?: string;
  status: UserStatus;
  roles: Role[];
  permissions: Permission[];
  lastLogin?: string;
  loginCount: number;
  failedLoginAttempts: number;
  accountLocked: boolean;
  emailVerified: boolean;
  phoneVerified: boolean;
  mfaEnabled: boolean;
  profile: UserProfile;
  preferences: UserPreferences;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface UserProfile {
  title?: string;
  department?: string;
  location?: string;
  timezone?: string;
  language?: string;
  phone?: string;
  address?: Address;
  socialLinks?: SocialLink[];
  bio?: string;
  skills?: string[];
  certifications?: Certification[];
  emergencyContact?: EmergencyContact;
}

export interface Address {
  street1: string;
  street2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface SocialLink {
  platform: string;
  url: string;
  verified: boolean;
}

export interface Certification {
  name: string;
  issuer: string;
  issuedAt: string;
  expiresAt?: string;
  credentialId?: string;
  url?: string;
}

export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
  email?: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  numberFormat: string;
  currency: string;
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  display: DisplayPreferences;
  accessibility: AccessibilityPreferences;
}

export interface NotificationPreferences {
  email: EmailNotifications;
  push: PushNotifications;
  sms: SmsNotifications;
  inApp: InAppNotifications;
  digest: DigestNotifications;
}

export interface EmailNotifications {
  enabled: boolean;
  frequency: NotificationFrequency;
  types: EmailNotificationType[];
  quietHours: QuietHours;
}

export interface PushNotifications {
  enabled: boolean;
  frequency: NotificationFrequency;
  types: PushNotificationType[];
  quietHours: QuietHours;
  sound: boolean;
  vibration: boolean;
}

export interface SmsNotifications {
  enabled: boolean;
  types: SmsNotificationType[];
  emergencyOnly: boolean;
}

export interface InAppNotifications {
  enabled: boolean;
  showDesktop: boolean;
  showMobile: boolean;
  duration: number;
  position: NotificationPosition;
}

export interface DigestNotifications {
  enabled: boolean;
  frequency: DigestFrequency;
  day: number;
  time: string;
  includeMetrics: boolean;
  includeSummary: boolean;
}

export interface QuietHours {
  enabled: boolean;
  start: string;
  end: string;
  timezone: string;
}

export interface PrivacyPreferences {
  showProfile: boolean;
  showActivity: boolean;
  showOnlineStatus: boolean;
  allowMessaging: boolean;
  allowDataExport: boolean;
  allowDataDeletion: boolean;
  trackingConsent: TrackingConsent;
}

export interface TrackingConsent {
  analytics: boolean;
  marketing: boolean;
  functional: boolean;
  performance: boolean;
  social: boolean;
}

export interface DisplayPreferences {
  density: 'compact' | 'normal' | 'comfortable';
  sidebarCollapsed: boolean;
  tablePageSize: number;
  showAvatars: boolean;
  showTooltips: boolean;
  showAnimations: boolean;
  showRichText: boolean;
  fontSize: FontSize;
  contrast: ContrastLevel;
}

export interface AccessibilityPreferences {
  screenReader: boolean;
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  keyboardNavigation: boolean;
  voiceControl: boolean;
  colorBlind: ColorBlindnessType;
  alternativeText: boolean;
}

export interface Role {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  type: RoleType;
  permissions: Permission[];
  hierarchy: number;
  isDefault: boolean;
  isSystem: boolean;
  isActive: boolean;
  conditions?: RoleCondition[];
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface Permission {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  resource: string;
  action: string;
  scope?: PermissionScope;
  conditions?: PermissionCondition[];
  granted: boolean;
  inherited?: boolean;
  source?: string;
  metadata?: Record<string, any>;
}

export interface RoleCondition {
  type: ConditionType;
  field: string;
  operator: ConditionOperator;
  value: any;
  description?: string;
}

export interface PermissionCondition {
  type: ConditionType;
  field: string;
  operator: ConditionOperator;
  value: any;
  description?: string;
}

export interface PermissionScope {
  type: ScopeType;
  value: string;
  description?: string;
}

// Audit and activity types
export interface AuditLog {
  id: string;
  userId?: string;
  userName?: string;
  sessionId?: string;
  action: AuditAction;
  resource: string;
  resourceId?: string;
  oldValue?: any;
  newValue?: any;
  result: AuditResult;
  reason?: string;
  ipAddress?: string;
  userAgent?: string;
  location?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface UserActivity {
  id: string;
  userId: string;
  sessionId?: string;
  type: ActivityType;
  action: string;
  resource?: string;
  details?: string;
  data?: Record<string, any>;
  duration?: number;
  ipAddress?: string;
  userAgent?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

// System and configuration types
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

// Form and input types
export interface FormField {
  key: string;
  label: string;
  type: FieldType;
  required?: boolean;
  placeholder?: string;
  helpText?: string;
  validation?: ValidationRule[];
  options?: FieldOption[];
  dependencies?: FieldDependency[];
  conditional?: FieldConditional[];
  metadata?: Record<string, any>;
}

export interface ValidationRule {
  type: ValidationType;
  value?: any;
  message: string;
  validator?: (value: any) => boolean | Promise<boolean>;
}

export interface FieldOption {
  label: string;
  value: any;
  disabled?: boolean;
  description?: string;
  group?: string;
  icon?: string;
}

export interface FieldDependency {
  field: string;
  value: any;
  operation: DependencyOperation;
}

export interface FieldConditional {
  condition: ConditionalExpression;
  action: ConditionalAction;
  target?: string;
}

export interface ConditionalExpression {
  field: string;
  operator: ConditionalOperator;
  value: any;
  logic?: 'and' | 'or';
  nested?: ConditionalExpression[];
}

export interface ConditionalAction {
  type: 'show' | 'hide' | 'enable' | 'disable' | 'require' | 'setValue';
  value?: any;
}

// Filter and search types
export interface FilterConfig {
  filters: Filter[];
  search?: SearchConfig;
  sorting?: SortConfig;
  grouping?: GroupConfig;
}

export interface Filter {
  key: string;
  label: string;
  type: FilterType;
  field: string;
  operator?: FilterOperator;
  value?: any;
  options?: FilterOption[];
  multiple?: boolean;
  clearable?: boolean;
  searchable?: boolean;
}

export interface SearchConfig {
  enabled: boolean;
  fields: string[];
  placeholder?: string;
  fuzzy?: boolean;
  minLength?: number;
  debounce?: number;
}

export interface SortConfig {
  field: string;
  direction: SortDirection;
  multiple?: boolean;
  priority?: number;
}

export interface GroupConfig {
  field: string;
  label?: string;
  direction?: SortDirection;
  collapsed?: boolean;
}

export interface FilterOption {
  label: string;
  value: any;
  count?: number;
  disabled?: boolean;
  description?: string;
}

// Table and list types
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
  render?: (value: any, record: any, index: number) => ReactNode;
  headerRender?: (column: TableColumn) => ReactNode;
  filterRender?: (column: TableColumn) => ReactNode;
  sorterRender?: (column: TableColumn) => ReactNode;
  ellipsis?: boolean;
  copyable?: boolean;
  editable?: boolean;
  required?: boolean;
  validation?: ValidationRule[];
}

export interface PaginationConfig {
  page: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: boolean;
  pageSizeOptions?: number[];
  simple?: boolean;
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
  filters?: Record<string, any>;
  formatting?: ExportFormatting;
  compression?: CompressionOptions;
  encryption?: EncryptionOptions;
}

export interface ExportSheet {
  name: string;
  data: any[];
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
  schema?: any;
  customValidators?: Record<string, (value: any) => boolean | string>;
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
  defaultValue?: any;
  required?: boolean;
}

export interface ImportProcessing {
  batchSize?: number;
  skipErrors?: boolean;
  updateExisting?: boolean;
  createMissing?: boolean;
  dryRun?: boolean;
}

// Enum and union types
export type UserStatus = 'active' | 'inactive' | 'pending' | 'blocked' | 'suspended' | 'archived';
export type RoleType = 'system' | 'custom' | 'temporary' | 'inherited';
export type ConditionType = 'time' | 'location' | 'device' | 'ip' | 'attribute' | 'custom';
export type ConditionOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'between';
export type ScopeType = 'global' | 'organization' | 'department' | 'team' | 'personal' | 'resource';
export type AuditAction = 'create' | 'read' | 'update' | 'delete' | 'login' | 'logout' | 'access' | 'export' | 'import' | 'configure';
export type AuditResult = 'success' | 'failure' | 'partial' | 'denied' | 'error';
export type ActivityType = 'navigation' | 'interaction' | 'api_call' | 'data_access' | 'configuration' | 'authentication' | 'security' | 'system';
export type Environment = 'development' | 'staging' | 'production' | 'test';
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
export type DependencyType = 'database' | 'api' | 'service' | 'storage' | 'cache' | 'queue' | 'external';
export type DependencyStatus = 'available' | 'unavailable' | 'degraded' | 'timeout' | 'error';
export type TimeRangePreset = 'last_hour' | 'last_24_hours' | 'last_7_days' | 'last_30_days' | 'last_90_days' | 'last_year' | 'this_week' | 'this_month' | 'this_year' | 'custom';
export type FieldType = 'text' | 'textarea' | 'email' | 'url' | 'password' | 'number' | 'phone' | 'date' | 'datetime' | 'time' | 'select' | 'multiselect' | 'checkbox' | 'radio' | 'switch' | 'slider' | 'file' | 'image' | 'color' | 'json' | 'custom';
export type ValidationType = 'required' | 'email' | 'url' | 'phone' | 'min' | 'max' | 'minLength' | 'maxLength' | 'pattern' | 'custom';
export type DependencyOperation = 'equals' | 'not_equals' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'contains' | 'not_contains';
export type ConditionalOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in' | 'is_empty' | 'is_not_empty';
export type FilterType = 'text' | 'select' | 'multiselect' | 'date' | 'daterange' | 'number' | 'numberrange' | 'boolean' | 'search';
export type FilterOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'between' | 'in' | 'not_in' | 'is_null' | 'is_not_null';
export type SortDirection = 'asc' | 'desc';
export type ExportType = 'csv' | 'excel' | 'pdf' | 'json' | 'xml' | 'txt';
export type ImportType = 'csv' | 'excel' | 'json' | 'xml' | 'txt';
export type NotificationFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly' | 'monthly';
export type EmailNotificationType = 'welcome' | 'security' | 'system' | 'reminders' | 'updates' | 'marketing';
export type PushNotificationType = 'alerts' | 'messages' | 'updates' | 'reminders' | 'security';
export type SmsNotificationType = 'security' | 'alerts' | 'verification' | 'emergency';
export type DigestFrequency = 'daily' | 'weekly' | 'monthly';
export type NotificationPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';
export type FontSize = 'small' | 'medium' | 'large' | 'extra-large';
export type ContrastLevel = 'normal' | 'high' | 'highest';
export type ColorBlindnessType = 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia' | 'achromatopsia';

// Additional supporting interfaces for specific configs
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
  conditions?: Record<string, any>;
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