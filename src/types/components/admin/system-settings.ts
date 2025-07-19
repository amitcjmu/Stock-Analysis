/**
 * Admin System Settings Component Types
 * 
 * Type definitions for system settings components including general settings,
 * security settings, and configuration management.
 */

import { ReactNode } from 'react';
import { BaseComponentProps } from '../shared';

// System Settings component types
export interface SystemSettingsProps extends BaseComponentProps {
  settings: SystemSettings;
  onUpdate: (updates: Partial<SystemSettings>) => void | Promise<void>;
  onReset?: (section?: string) => void | Promise<void>;
  onExport?: () => void;
  onImport?: (file: File) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
  sections?: SettingsSection[];
  activeSection?: string;
  onSectionChange?: (section: string) => void;
  validation?: SettingsValidationConfig;
  autoSave?: boolean;
  autoSaveInterval?: number;
  onAutoSave?: (updates: Partial<SystemSettings>) => void;
  showNavigation?: boolean;
  showActions?: boolean;
  showValidation?: boolean;
  showDirtyIndicator?: boolean;
  enableReset?: boolean;
  enableExport?: boolean;
  enableImport?: boolean;
  enableAuditLog?: boolean;
  auditLogs?: SettingsAuditLog[];
  onAuditLogRefresh?: () => void;
  renderSection?: (section: SettingsSection, settings: SystemSettings) => ReactNode;
  renderNavigation?: (sections: SettingsSection[], activeSection: string) => ReactNode;
  renderActions?: (hasChanges: boolean) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  layout?: 'sidebar' | 'tabs' | 'accordion' | 'wizard';
  variant?: 'default' | 'compact' | 'detailed';
}

export interface SecuritySettingsProps extends BaseComponentProps {
  settings: SecuritySettings;
  onUpdate: (updates: Partial<SecuritySettings>) => void | Promise<void>;
  loading?: boolean;
  error?: string | null;
  policies?: SecurityPolicy[];
  onPolicyCreate?: (policy: SecurityPolicy) => void | Promise<void>;
  onPolicyUpdate?: (policy: SecurityPolicy) => void | Promise<void>;
  onPolicyDelete?: (policy: SecurityPolicy) => void | Promise<void>;
  auditLogs?: SecurityAuditLog[];
  onAuditLogRefresh?: () => void;
  showPasswordPolicy?: boolean;
  showSessionSettings?: boolean;
  showMFASettings?: boolean;
  showAccessControl?: boolean;
  showEncryption?: boolean;
  showAuditLog?: boolean;
  showPolicies?: boolean;
  enableTestMode?: boolean;
  onTestPolicy?: (policy: SecurityPolicy) => void | Promise<void>;
  renderPolicyForm?: (policy: SecurityPolicy | null, onSubmit: (policy: SecurityPolicy) => void) => ReactNode;
  renderAuditLog?: (logs: SecurityAuditLog[]) => ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  variant?: 'default' | 'advanced' | 'compliance';
}

// Supporting types for System Settings
export interface SystemSettings {
  general: GeneralSettings;
  security: SecuritySettings;
  notifications: NotificationSettings;
  api: ApiSettings;
  storage: StorageSettings;
  performance: PerformanceSettings;
  features: FeatureSettings;
  branding: BrandingSettings;
  maintenance: MaintenanceSettings;
  backup: BackupSettings;
}

export interface GeneralSettings {
  siteName: string;
  siteDescription?: string;
  siteUrl: string;
  timezone: string;
  language: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  currency: string;
  allowRegistration: boolean;
  requireEmailVerification: boolean;
  defaultUserRole: string;
  maxFileUploadSize: number;
  allowedFileTypes: string[];
}

export interface SecuritySettings {
  passwordPolicy: PasswordPolicy;
  sessionSettings: SessionSettings;
  mfaSettings: MfaSettings;
  accessControl: AccessControlSettings;
  encryption: EncryptionSettings;
  rateLimiting: RateLimitSettings;
  ipWhitelist: string[];
  ipBlacklist: string[];
  corsSettings: CorsSettings;
}

export interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  maxAge: number;
  preventReuse: number;
  lockoutThreshold: number;
  lockoutDuration: number;
}

export interface SessionSettings {
  timeout: number;
  extendOnActivity: boolean;
  maxConcurrentSessions: number;
  allowMultipleDevices: boolean;
  forceLogoutOnPasswordChange: boolean;
  rememberMeDuration: number;
}

export interface MfaSettings {
  enabled: boolean;
  required: boolean;
  methods: MfaMethod[];
  backupCodes: boolean;
  gracePeriod: number;
  trustedDevices: boolean;
  trustedDeviceDuration: number;
}

export interface AccessControlSettings {
  rbacEnabled: boolean;
  inheritPermissions: boolean;
  denyByDefault: boolean;
  auditAccessAttempts: boolean;
  ipBasedRestrictions: boolean;
  timeBasedRestrictions: boolean;
  deviceBasedRestrictions: boolean;
}

export interface EncryptionSettings {
  algorithm: string;
  keySize: number;
  rotationInterval: number;
  encryptAtRest: boolean;
  encryptInTransit: boolean;
  hashingAlgorithm: string;
  saltRounds: number;
}

export interface RateLimitSettings {
  enabled: boolean;
  requestsPerMinute: number;
  requestsPerHour: number;
  requestsPerDay: number;
  blockDuration: number;
  exemptIps: string[];
  exemptUsers: string[];
}

export interface CorsSettings {
  enabled: boolean;
  allowedOrigins: string[];
  allowedMethods: string[];
  allowedHeaders: string[];
  allowCredentials: boolean;
  maxAge: number;
}

export interface NotificationSettings {
  email: EmailNotificationSettings;
  push: PushNotificationSettings;
  sms: SmsNotificationSettings;
  inApp: InAppNotificationSettings;
  webhooks: WebhookSettings[];
}

export interface EmailNotificationSettings {
  enabled: boolean;
  smtpHost: string;
  smtpPort: number;
  smtpSecure: boolean;
  smtpUser: string;
  smtpPassword: string;
  fromAddress: string;
  fromName: string;
  templates: EmailTemplate[];
}

export interface ApiSettings {
  version: string;
  baseUrl: string;
  timeout: number;
  retries: number;
  rateLimit: ApiRateLimit;
  authentication: ApiAuthentication;
  documentation: ApiDocumentation;
  cors: CorsSettings;
  compression: boolean;
  caching: ApiCaching;
}

export interface StorageSettings {
  provider: 'local' | 's3' | 'gcs' | 'azure';
  localPath?: string;
  s3Settings?: S3Settings;
  gcsSettings?: GcsSettings;
  azureSettings?: AzureSettings;
  maxFileSize: number;
  allowedTypes: string[];
  encryption: boolean;
  compression: boolean;
  cdn: CdnSettings;
}

export interface PerformanceSettings {
  caching: CacheSettings;
  compression: CompressionSettings;
  minification: boolean;
  lazyLoading: boolean;
  cdnEnabled: boolean;
  cdnUrl?: string;
  optimizeImages: boolean;
  databaseOptimization: DatabaseOptimization;
}

export interface FeatureSettings {
  features: Feature[];
  experiments: Experiment[];
  toggles: FeatureToggle[];
  rollouts: FeatureRollout[];
}

export interface BrandingSettings {
  logo?: string;
  favicon?: string;
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  customCss?: string;
  footerText?: string;
  supportEmail: string;
  supportUrl?: string;
}

export interface MaintenanceSettings {
  enabled: boolean;
  message: string;
  startTime?: string;
  endTime?: string;
  allowedIps: string[];
  showCountdown: boolean;
  redirectUrl?: string;
}

export interface BackupSettings {
  enabled: boolean;
  frequency: BackupFrequency;
  retention: number;
  storage: BackupStorage;
  encryption: boolean;
  compression: boolean;
  includeFiles: boolean;
  includeDatabases: boolean;
  notifications: BackupNotifications;
}

export interface SettingsSection {
  key: string;
  title: string;
  description?: string;
  icon?: string;
  order: number;
  permissions?: string[];
  fields: SettingsField[];
}

export interface SettingsField {
  key: string;
  label: string;
  type: SettingsFieldType;
  description?: string;
  placeholder?: string;
  required?: boolean;
  validation?: SettingsValidationRule[];
  options?: FieldOption[];
  dependencies?: FieldDependency[];
  group?: string;
  order: number;
}

export interface SettingsValidationConfig {
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  showErrors?: boolean;
  stopOnFirstError?: boolean;
  customValidators?: Record<string, (value: any) => boolean | string>;
}

export interface SettingsValidationRule {
  type: 'required' | 'email' | 'url' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message: string;
  validator?: (value: any) => boolean | Promise<boolean>;
}

export interface SettingsAuditLog {
  id: string;
  userId: string;
  userName: string;
  action: SettingsAction;
  section: string;
  field?: string;
  oldValue?: any;
  newValue?: any;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
  metadata?: Record<string, any>;
}

export interface SecurityPolicy {
  id: string;
  name: string;
  description?: string;
  type: SecurityPolicyType;
  rules: SecurityRule[];
  enabled: boolean;
  priority: number;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface SecurityRule {
  id: string;
  condition: SecurityCondition;
  action: SecurityAction;
  parameters?: Record<string, any>;
  enabled: boolean;
}

export interface SecurityAuditLog {
  id: string;
  userId?: string;
  userName?: string;
  action: SecurityAction;
  resource: string;
  result: 'success' | 'failure' | 'denied';
  reason?: string;
  timestamp: string;
  ipAddress?: string;
  userAgent?: string;
  metadata?: Record<string, any>;
}

// Supporting enum and union types
export type SettingsFieldType = 
  | 'text' 
  | 'textarea' 
  | 'email' 
  | 'url' 
  | 'password' 
  | 'number' 
  | 'boolean' 
  | 'select' 
  | 'multiselect' 
  | 'date' 
  | 'time' 
  | 'datetime' 
  | 'file' 
  | 'color' 
  | 'json';

export type SettingsAction = 
  | 'create' 
  | 'read' 
  | 'update' 
  | 'delete' 
  | 'export' 
  | 'import' 
  | 'reset';

export type SecurityPolicyType = 
  | 'authentication' 
  | 'authorization' 
  | 'data_protection' 
  | 'network_security' 
  | 'compliance';

export type SecurityCondition = 
  | 'ip_address' 
  | 'user_role' 
  | 'time_range' 
  | 'device_type' 
  | 'location' 
  | 'custom';

export type SecurityAction = 
  | 'allow' 
  | 'deny' 
  | 'require_mfa' 
  | 'log' 
  | 'alert' 
  | 'block' 
  | 'redirect';

export type MfaMethod = 
  | 'totp' 
  | 'sms' 
  | 'email' 
  | 'hardware_token' 
  | 'biometric';

export type BackupFrequency = 
  | 'hourly' 
  | 'daily' 
  | 'weekly' 
  | 'monthly';

export type BackupStorage = 
  | 'local' 
  | 's3' 
  | 'gcs' 
  | 'azure' 
  | 'ftp';

// Additional supporting interfaces
export interface MfaMethod {
  type: string;
  enabled: boolean;
  configuration?: Record<string, any>;
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  body: string;
  variables: string[];
}

export interface PushNotificationSettings {
  enabled: boolean;
  provider: string;
  apiKey: string;
  configuration?: Record<string, any>;
}

export interface SmsNotificationSettings {
  enabled: boolean;
  provider: string;
  apiKey: string;
  fromNumber: string;
  configuration?: Record<string, any>;
}

export interface InAppNotificationSettings {
  enabled: boolean;
  showDesktop: boolean;
  showMobile: boolean;
  retention: number;
  maxPerUser: number;
}

export interface WebhookSettings {
  id: string;
  name: string;
  url: string;
  events: string[];
  headers?: Record<string, string>;
  secret?: string;
  enabled: boolean;
}

export interface ApiRateLimit {
  requestsPerMinute: number;
  requestsPerHour: number;
  burstLimit: number;
}

export interface ApiAuthentication {
  methods: string[];
  tokenExpiry: number;
  refreshTokenExpiry: number;
  allowApiKeys: boolean;
}

export interface ApiDocumentation {
  enabled: boolean;
  path: string;
  version: string;
  title: string;
  description: string;
}

export interface ApiCaching {
  enabled: boolean;
  defaultTtl: number;
  maxTtl: number;
  strategy: 'memory' | 'redis' | 'database';
}

export interface S3Settings {
  bucket: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  endpoint?: string;
}

export interface GcsSettings {
  bucket: string;
  projectId: string;
  keyFile: string;
}

export interface AzureSettings {
  container: string;
  accountName: string;
  accountKey: string;
}

export interface CdnSettings {
  enabled: boolean;
  url: string;
  provider: string;
  configuration?: Record<string, any>;
}

export interface CacheSettings {
  enabled: boolean;
  provider: 'memory' | 'redis' | 'memcached';
  ttl: number;
  maxSize: number;
  compression: boolean;
}

export interface CompressionSettings {
  enabled: boolean;
  algorithm: 'gzip' | 'brotli' | 'deflate';
  level: number;
  threshold: number;
}

export interface DatabaseOptimization {
  enabled: boolean;
  indexOptimization: boolean;
  queryOptimization: boolean;
  connectionPooling: boolean;
  maxConnections: number;
}

export interface Feature {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  dependencies?: string[];
  configuration?: Record<string, any>;
}

export interface Experiment {
  id: string;
  name: string;
  description?: string;
  active: boolean;
  variants: ExperimentVariant[];
  allocation: number;
  startDate?: string;
  endDate?: string;
}

export interface ExperimentVariant {
  id: string;
  name: string;
  allocation: number;
  configuration?: Record<string, any>;
}

export interface FeatureToggle {
  id: string;
  name: string;
  enabled: boolean;
  conditions?: ToggleCondition[];
}

export interface ToggleCondition {
  type: 'user' | 'role' | 'percentage' | 'custom';
  value: any;
  operator?: 'equals' | 'in' | 'greater_than' | 'less_than';
}

export interface FeatureRollout {
  id: string;
  featureId: string;
  percentage: number;
  targetUsers?: string[];
  targetRoles?: string[];
  startDate?: string;
  endDate?: string;
}

export interface BackupNotifications {
  onSuccess: boolean;
  onFailure: boolean;
  recipients: string[];
}

export interface FieldOption {
  label: string;
  value: any;
  disabled?: boolean;
  description?: string;
}

export interface FieldDependency {
  field: string;
  value: any;
  operation: 'equals' | 'not_equals' | 'in' | 'not_in';
}