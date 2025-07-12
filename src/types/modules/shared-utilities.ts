/**
 * Shared Utilities Module Namespace
 * 
 * TypeScript module boundaries for shared utilities and cross-cutting concerns.
 * Provides type definitions for common utilities, helpers, and shared components.
 */

import { ReactNode } from 'react';

// Base shared types
export interface BaseUtilityProps {
  className?: string;
  children?: ReactNode;
}

export interface ConfigurationOptions {
  [key: string]: any;
}

export interface ErrorContext {
  component?: string;
  action?: string;
  userId?: string;
  flowId?: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

// Shared Utilities namespace declaration
declare namespace SharedUtilities {
  // Authentication & Authorization namespace
  namespace Auth {
    interface AuthenticationService {
      login: (credentials: LoginCredentials) => Promise<AuthResult>;
      logout: () => Promise<void>;
      refreshToken: (token: string) => Promise<AuthResult>;
      validateToken: (token: string) => Promise<TokenValidation>;
      getCurrentUser: () => Promise<User>;
      updateProfile: (updates: Partial<UserProfile>) => Promise<UserProfile>;
      changePassword: (request: PasswordChangeRequest) => Promise<void>;
      resetPassword: (request: PasswordResetRequest) => Promise<void>;
    }

    interface AuthorizationService {
      hasPermission: (permission: string, context?: AuthContext) => boolean;
      hasRole: (role: string, context?: AuthContext) => boolean;
      canAccess: (resource: string, action: string, context?: AuthContext) => boolean;
      getPermissions: (userId: string, context?: AuthContext) => Promise<Permission[]>;
      getRoles: (userId: string, context?: AuthContext) => Promise<Role[]>;
      checkResourceAccess: (resourceId: string, action: string) => Promise<boolean>;
    }

    interface MultiTenantService {
      getCurrentTenant: () => Promise<Tenant>;
      switchTenant: (tenantId: string) => Promise<void>;
      getTenantContext: () => TenantContext;
      validateTenantAccess: (tenantId: string) => Promise<boolean>;
      getTenantSettings: (tenantId: string) => Promise<TenantSettings>;
      updateTenantSettings: (tenantId: string, updates: Partial<TenantSettings>) => Promise<void>;
    }

    interface SessionService {
      createSession: (userId: string, metadata?: Record<string, any>) => Promise<Session>;
      getSession: (sessionId: string) => Promise<Session>;
      updateSession: (sessionId: string, updates: Partial<Session>) => Promise<void>;
      destroySession: (sessionId: string) => Promise<void>;
      validateSession: (sessionId: string) => Promise<SessionValidation>;
      extendSession: (sessionId: string, duration: number) => Promise<void>;
    }

    // Auth Models
    interface LoginCredentials {
      username: string;
      password: string;
      tenantId?: string;
      mfaCode?: string;
      rememberMe?: boolean;
    }

    interface AuthResult {
      success: boolean;
      user: User;
      tokens: AuthTokens;
      permissions: Permission[];
      roles: Role[];
      tenantContext: TenantContext;
      expiresAt: string;
    }

    interface TokenValidation {
      isValid: boolean;
      user?: User;
      permissions?: Permission[];
      roles?: Role[];
      expiresAt?: string;
      error?: string;
    }

    interface User {
      id: string;
      username: string;
      email: string;
      firstName: string;
      lastName: string;
      status: 'active' | 'inactive' | 'suspended';
      lastLogin: string;
      createdAt: string;
      updatedAt: string;
      profile: UserProfile;
    }

    interface UserProfile {
      id: string;
      userId: string;
      displayName: string;
      avatar?: string;
      timezone: string;
      language: string;
      preferences: UserPreferences;
      notifications: NotificationSettings;
      security: SecuritySettings;
    }

    interface AuthTokens {
      accessToken: string;
      refreshToken: string;
      tokenType: 'Bearer';
      expiresIn: number;
      scope: string;
    }

    interface Permission {
      id: string;
      name: string;
      description: string;
      resource: string;
      actions: string[];
      conditions?: PermissionCondition[];
    }

    interface Role {
      id: string;
      name: string;
      description: string;
      permissions: Permission[];
      inherits: string[];
      context: 'global' | 'tenant' | 'engagement';
    }

    interface AuthContext {
      tenantId?: string;
      engagementId?: string;
      resourceId?: string;
      metadata?: Record<string, any>;
    }

    interface Tenant {
      id: string;
      name: string;
      subdomain: string;
      status: 'active' | 'inactive' | 'suspended';
      settings: TenantSettings;
      limits: TenantLimits;
      createdAt: string;
      updatedAt: string;
    }

    interface TenantContext {
      tenantId: string;
      tenantName: string;
      engagementId?: string;
      userId: string;
      permissions: Permission[];
      roles: Role[];
      settings: TenantSettings;
    }

    interface TenantSettings {
      branding: BrandingSettings;
      security: SecuritySettings;
      features: FeatureSettings;
      integrations: IntegrationSettings;
      notifications: NotificationSettings;
    }

    interface Session {
      id: string;
      userId: string;
      tenantId: string;
      status: 'active' | 'expired' | 'terminated';
      createdAt: string;
      lastAccessAt: string;
      expiresAt: string;
      ipAddress: string;
      userAgent: string;
      metadata: Record<string, any>;
    }

    interface SessionValidation {
      isValid: boolean;
      session?: Session;
      user?: User;
      tenant?: Tenant;
      error?: string;
    }

    interface PasswordChangeRequest {
      currentPassword: string;
      newPassword: string;
      confirmPassword: string;
    }

    interface PasswordResetRequest {
      email: string;
      token?: string;
      newPassword?: string;
    }

    interface PermissionCondition {
      field: string;
      operator: 'eq' | 'ne' | 'in' | 'not_in' | 'gt' | 'lt' | 'gte' | 'lte';
      value: any;
    }

    interface TenantLimits {
      maxUsers: number;
      maxEngagements: number;
      maxFlows: number;
      maxStorage: number;
      maxApiCalls: number;
    }

    interface BrandingSettings {
      logo?: string;
      favicon?: string;
      primaryColor: string;
      secondaryColor: string;
      fontFamily: string;
      customCSS?: string;
    }

    interface SecuritySettings {
      passwordPolicy: PasswordPolicy;
      sessionTimeout: number;
      mfaRequired: boolean;
      mfaMethods: string[];
      ipWhitelist: string[];
      auditLogging: boolean;
    }

    interface FeatureSettings {
      enabledFeatures: string[];
      disabledFeatures: string[];
      betaFeatures: string[];
      limits: Record<string, number>;
    }

    interface IntegrationSettings {
      enabledIntegrations: string[];
      configurations: Record<string, any>;
      webhooks: WebhookConfig[];
    }

    interface NotificationSettings {
      emailEnabled: boolean;
      smsEnabled: boolean;
      pushEnabled: boolean;
      channels: NotificationChannel[];
      preferences: NotificationPreferences;
    }

    interface UserPreferences {
      theme: 'light' | 'dark' | 'auto';
      dateFormat: string;
      timeFormat: string;
      numberFormat: string;
      pageSize: number;
      autoSave: boolean;
      shortcuts: Record<string, string>;
    }

    interface PasswordPolicy {
      minLength: number;
      requireUppercase: boolean;
      requireLowercase: boolean;
      requireNumbers: boolean;
      requireSpecialChars: boolean;
      maxAge: number;
      historySize: number;
    }

    interface WebhookConfig {
      id: string;
      name: string;
      url: string;
      events: string[];
      headers: Record<string, string>;
      secret: string;
      active: boolean;
    }

    interface NotificationChannel {
      id: string;
      type: 'email' | 'sms' | 'push' | 'slack' | 'webhook';
      name: string;
      configuration: Record<string, any>;
      enabled: boolean;
    }

    interface NotificationPreferences {
      email: boolean;
      sms: boolean;
      push: boolean;
      frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
      categories: Record<string, boolean>;
    }
  }

  // API Utilities namespace
  namespace API {
    interface ApiClientService {
      get: <T>(url: string, options?: RequestOptions) => Promise<ApiResponse<T>>;
      post: <T>(url: string, data?: any, options?: RequestOptions) => Promise<ApiResponse<T>>;
      put: <T>(url: string, data?: any, options?: RequestOptions) => Promise<ApiResponse<T>>;
      patch: <T>(url: string, data?: any, options?: RequestOptions) => Promise<ApiResponse<T>>;
      delete: <T>(url: string, options?: RequestOptions) => Promise<ApiResponse<T>>;
      upload: <T>(url: string, file: File, options?: UploadOptions) => Promise<ApiResponse<T>>;
      download: (url: string, options?: DownloadOptions) => Promise<Blob>;
    }

    interface RequestInterceptorService {
      addRequestInterceptor: (interceptor: RequestInterceptor) => string;
      removeRequestInterceptor: (id: string) => void;
      addResponseInterceptor: (interceptor: ResponseInterceptor) => string;
      removeResponseInterceptor: (id: string) => void;
    }

    interface CacheService {
      get: <T>(key: string) => Promise<T | null>;
      set: <T>(key: string, value: T, ttl?: number) => Promise<void>;
      delete: (key: string) => Promise<void>;
      clear: () => Promise<void>;
      has: (key: string) => Promise<boolean>;
      keys: (pattern?: string) => Promise<string[]>;
    }

    interface RetryService {
      retry: <T>(fn: () => Promise<T>, options?: RetryOptions) => Promise<T>;
      withRetry: <T>(options: RetryOptions) => (fn: () => Promise<T>) => Promise<T>;
      isRetryable: (error: Error) => boolean;
      getBackoffDelay: (attempt: number, options: RetryOptions) => number;
    }

    // API Models
    interface ApiResponse<T = any> {
      success: boolean;
      data: T;
      message?: string;
      errors?: ApiError[];
      metadata?: ResponseMetadata;
      pagination?: PaginationInfo;
    }

    interface ApiError {
      code: string;
      message: string;
      field?: string;
      details?: Record<string, any>;
    }

    interface ResponseMetadata {
      requestId: string;
      timestamp: string;
      version: string;
      processingTime: number;
      rateLimit?: RateLimitInfo;
    }

    interface PaginationInfo {
      page: number;
      pageSize: number;
      total: number;
      totalPages: number;
      hasNext: boolean;
      hasPrevious: boolean;
    }

    interface RequestOptions {
      headers?: Record<string, string>;
      timeout?: number;
      retries?: number;
      cache?: boolean;
      cacheTtl?: number;
      validateStatus?: (status: number) => boolean;
      transformRequest?: (data: any) => any;
      transformResponse?: (data: any) => any;
    }

    interface UploadOptions extends RequestOptions {
      onProgress?: (progress: ProgressEvent) => void;
      chunkSize?: number;
      resumable?: boolean;
    }

    interface DownloadOptions extends RequestOptions {
      onProgress?: (progress: ProgressEvent) => void;
      fileName?: string;
      mimeType?: string;
    }

    interface RequestInterceptor {
      onRequest: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
      onRequestError: (error: Error) => Promise<Error>;
    }

    interface ResponseInterceptor {
      onResponse: (response: Response) => Response | Promise<Response>;
      onResponseError: (error: Error) => Promise<Error>;
    }

    interface RetryOptions {
      maxRetries: number;
      initialDelay: number;
      maxDelay: number;
      backoffFactor: number;
      jitter: boolean;
      retryableErrors: string[];
      onRetry?: (error: Error, attempt: number) => void;
    }

    interface RequestConfig {
      url: string;
      method: string;
      headers: Record<string, string>;
      data?: any;
      params?: Record<string, any>;
      timeout: number;
      baseURL?: string;
    }

    interface RateLimitInfo {
      limit: number;
      remaining: number;
      reset: number;
      retryAfter?: number;
    }

    interface Response {
      data: any;
      status: number;
      statusText: string;
      headers: Record<string, string>;
      config: RequestConfig;
    }
  }

  // Validation Utilities namespace
  namespace Validation {
    interface ValidationService {
      validate: (data: any, schema: ValidationSchema) => ValidationResult;
      validateAsync: (data: any, schema: ValidationSchema) => Promise<ValidationResult>;
      createSchema: (definition: SchemaDefinition) => ValidationSchema;
      addRule: (name: string, rule: ValidationRule) => void;
      removeRule: (name: string) => void;
      getRule: (name: string) => ValidationRule | undefined;
    }

    interface SanitizationService {
      sanitize: (data: any, rules: SanitizationRules) => any;
      sanitizeHtml: (html: string, options?: HtmlSanitizationOptions) => string;
      sanitizeInput: (input: string, type: InputType) => string;
      preventXSS: (input: string) => string;
      preventSQLInjection: (input: string) => string;
    }

    interface FormValidationService {
      validateForm: (formData: FormData, schema: FormSchema) => FormValidationResult;
      validateField: (fieldName: string, value: any, rules: FieldRules) => FieldValidationResult;
      createFormSchema: (fields: FieldDefinition[]) => FormSchema;
      addFieldRule: (fieldName: string, rule: FieldRule) => void;
      removeFieldRule: (fieldName: string, ruleName: string) => void;
    }

    // Validation Models
    interface ValidationResult {
      isValid: boolean;
      errors: ValidationError[];
      warnings: ValidationWarning[];
      data?: any;
      metadata?: Record<string, any>;
    }

    interface ValidationSchema {
      type: 'object' | 'array' | 'string' | 'number' | 'boolean' | 'date';
      properties?: Record<string, ValidationSchema>;
      items?: ValidationSchema;
      rules: ValidationRule[];
      required?: string[];
      optional?: string[];
    }

    interface ValidationRule {
      name: string;
      validate: (value: any, context?: ValidationContext) => boolean | Promise<boolean>;
      message: string;
      parameters?: Record<string, any>;
      severity: 'error' | 'warning' | 'info';
    }

    interface ValidationError {
      field: string;
      message: string;
      code: string;
      value: any;
      severity: 'error' | 'warning' | 'info';
      metadata?: Record<string, any>;
    }

    interface ValidationWarning {
      field: string;
      message: string;
      code: string;
      value: any;
      suggestion?: string;
      metadata?: Record<string, any>;
    }

    interface ValidationContext {
      parentValue?: any;
      rootValue?: any;
      path: string[];
      metadata?: Record<string, any>;
    }

    interface SchemaDefinition {
      type: string;
      properties?: Record<string, SchemaDefinition>;
      items?: SchemaDefinition;
      rules?: string[];
      required?: string[];
      optional?: string[];
      metadata?: Record<string, any>;
    }

    interface SanitizationRules {
      [field: string]: SanitizationRule[];
    }

    interface SanitizationRule {
      type: 'trim' | 'lowercase' | 'uppercase' | 'escape' | 'strip' | 'replace' | 'custom';
      parameters?: Record<string, any>;
      apply: (value: any, parameters?: Record<string, any>) => any;
    }

    interface HtmlSanitizationOptions {
      allowedTags: string[];
      allowedAttributes: Record<string, string[]>;
      allowedSchemes: string[];
      stripTags: boolean;
      stripAttributes: boolean;
    }

    interface FormData {
      [field: string]: any;
    }

    interface FormSchema {
      fields: Record<string, FieldSchema>;
      rules: FormRule[];
      metadata?: Record<string, any>;
    }

    interface FieldSchema {
      type: string;
      rules: FieldRule[];
      required: boolean;
      label: string;
      placeholder?: string;
      defaultValue?: any;
      metadata?: Record<string, any>;
    }

    interface FormValidationResult {
      isValid: boolean;
      errors: Record<string, FieldValidationResult>;
      warnings: Record<string, FieldValidationResult>;
      data: FormData;
      metadata?: Record<string, any>;
    }

    interface FieldValidationResult {
      isValid: boolean;
      errors: ValidationError[];
      warnings: ValidationWarning[];
      value: any;
    }

    interface FieldDefinition {
      name: string;
      type: string;
      label: string;
      required: boolean;
      rules: FieldRule[];
      placeholder?: string;
      defaultValue?: any;
      metadata?: Record<string, any>;
    }

    interface FieldRules {
      [ruleName: string]: FieldRule;
    }

    interface FieldRule {
      name: string;
      validate: (value: any, context?: FieldValidationContext) => boolean | Promise<boolean>;
      message: string;
      parameters?: Record<string, any>;
      severity: 'error' | 'warning' | 'info';
    }

    interface FormRule {
      name: string;
      validate: (formData: FormData, context?: FormValidationContext) => boolean | Promise<boolean>;
      message: string;
      parameters?: Record<string, any>;
      severity: 'error' | 'warning' | 'info';
    }

    interface FieldValidationContext {
      fieldName: string;
      formData: FormData;
      metadata?: Record<string, any>;
    }

    interface FormValidationContext {
      formData: FormData;
      metadata?: Record<string, any>;
    }

    type InputType = 'text' | 'email' | 'url' | 'number' | 'phone' | 'html' | 'json' | 'sql';
  }

  // Error Handling namespace
  namespace ErrorHandling {
    interface ErrorService {
      handleError: (error: Error, context?: ErrorContext) => void;
      reportError: (error: Error, context?: ErrorContext) => Promise<void>;
      logError: (error: Error, context?: ErrorContext) => void;
      createError: (message: string, code?: string, details?: Record<string, any>) => AppError;
      isRetryableError: (error: Error) => boolean;
      getErrorSeverity: (error: Error) => ErrorSeverity;
    }

    interface ErrorBoundaryService {
      captureError: (error: Error, errorInfo: ErrorInfo) => void;
      reportErrorBoundary: (error: Error, errorInfo: ErrorInfo) => Promise<void>;
      getErrorFallback: (error: Error, errorInfo: ErrorInfo) => ReactNode;
      resetErrorBoundary: () => void;
    }

    interface ErrorRecoveryService {
      attemptRecovery: (error: Error, strategy: RecoveryStrategy) => Promise<boolean>;
      getRecoveryStrategies: (error: Error) => RecoveryStrategy[];
      executeRecovery: (strategy: RecoveryStrategy) => Promise<void>;
      canRecover: (error: Error) => boolean;
    }

    // Error Models
    interface AppError extends Error {
      code: string;
      severity: ErrorSeverity;
      context?: ErrorContext;
      details?: Record<string, any>;
      timestamp: string;
      userId?: string;
      sessionId?: string;
      requestId?: string;
      stack?: string;
      cause?: Error;
    }

    interface ErrorInfo {
      componentStack: string;
      errorBoundary?: string;
      errorBoundaryStack?: string;
    }

    interface RecoveryStrategy {
      name: string;
      description: string;
      priority: number;
      execute: () => Promise<void>;
      canExecute: (error: Error) => boolean;
      maxAttempts: number;
      currentAttempts: number;
    }

    interface ErrorReport {
      id: string;
      error: AppError;
      context: ErrorContext;
      timestamp: string;
      userAgent: string;
      url: string;
      userId?: string;
      sessionId?: string;
      stackTrace: string;
      breadcrumbs: ErrorBreadcrumb[];
      metadata: Record<string, any>;
    }

    interface ErrorBreadcrumb {
      timestamp: string;
      message: string;
      category: string;
      level: 'info' | 'warning' | 'error';
      data?: Record<string, any>;
    }

    type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';
  }

  // Utility Functions namespace
  namespace Utils {
    interface DateUtilityService {
      formatDate: (date: Date | string, format: string) => string;
      parseDate: (dateString: string, format?: string) => Date;
      addDays: (date: Date, days: number) => Date;
      subtractDays: (date: Date, days: number) => Date;
      diffDays: (date1: Date, date2: Date) => number;
      isValidDate: (date: any) => boolean;
      getTimeAgo: (date: Date) => string;
      getTimezone: () => string;
      convertTimezone: (date: Date, timezone: string) => Date;
    }

    interface StringUtilityService {
      capitalize: (str: string) => string;
      camelCase: (str: string) => string;
      kebabCase: (str: string) => string;
      snakeCase: (str: string) => string;
      truncate: (str: string, length: number, suffix?: string) => string;
      slugify: (str: string) => string;
      stripHtml: (html: string) => string;
      escapeHtml: (html: string) => string;
      unescapeHtml: (html: string) => string;
      isEmail: (email: string) => boolean;
      isUrl: (url: string) => boolean;
      generateId: (prefix?: string) => string;
      generateSlug: (text: string) => string;
    }

    interface NumberUtilityService {
      formatNumber: (num: number, options?: NumberFormatOptions) => string;
      formatCurrency: (amount: number, currency: string, options?: CurrencyFormatOptions) => string;
      formatPercentage: (value: number, decimals?: number) => string;
      formatBytes: (bytes: number, decimals?: number) => string;
      clamp: (value: number, min: number, max: number) => number;
      round: (value: number, decimals: number) => number;
      isNumber: (value: any) => boolean;
      isInteger: (value: any) => boolean;
      isFloat: (value: any) => boolean;
      randomInt: (min: number, max: number) => number;
      randomFloat: (min: number, max: number) => number;
    }

    interface ArrayUtilityService {
      chunk: <T>(array: T[], size: number) => T[][];
      flatten: <T>(array: (T | T[])[], depth?: number) => T[];
      unique: <T>(array: T[], key?: keyof T) => T[];
      groupBy: <T>(array: T[], key: keyof T) => Record<string, T[]>;
      sortBy: <T>(array: T[], key: keyof T, order?: 'asc' | 'desc') => T[];
      shuffle: <T>(array: T[]) => T[];
      sample: <T>(array: T[], count?: number) => T | T[];
      difference: <T>(array1: T[], array2: T[]) => T[];
      intersection: <T>(array1: T[], array2: T[]) => T[];
      union: <T>(array1: T[], array2: T[]) => T[];
      isEmpty: (array: any[]) => boolean;
      isEqual: (array1: any[], array2: any[]) => boolean;
    }

    interface ObjectUtilityService {
      clone: <T>(obj: T) => T;
      merge: <T>(target: T, ...sources: Partial<T>[]) => T;
      pick: <T, K extends keyof T>(obj: T, keys: K[]) => Pick<T, K>;
      omit: <T, K extends keyof T>(obj: T, keys: K[]) => Omit<T, K>;
      has: (obj: any, path: string) => boolean;
      get: (obj: any, path: string, defaultValue?: any) => any;
      set: (obj: any, path: string, value: any) => void;
      isEmpty: (obj: any) => boolean;
      isEqual: (obj1: any, obj2: any) => boolean;
      keys: (obj: any) => string[];
      values: (obj: any) => any[];
      entries: (obj: any) => [string, any][];
      invert: (obj: Record<string, any>) => Record<string, string>;
    }

    interface ColorUtilityService {
      hexToRgb: (hex: string) => RGB;
      rgbToHex: (r: number, g: number, b: number) => string;
      hslToRgb: (h: number, s: number, l: number) => RGB;
      rgbToHsl: (r: number, g: number, b: number) => HSL;
      darken: (color: string, amount: number) => string;
      lighten: (color: string, amount: number) => string;
      contrast: (color1: string, color2: string) => number;
      isValidColor: (color: string) => boolean;
      randomColor: () => string;
      getColorPalette: (baseColor: string, count: number) => string[];
    }

    // Utility Models
    interface NumberFormatOptions {
      locale?: string;
      minimumFractionDigits?: number;
      maximumFractionDigits?: number;
      useGrouping?: boolean;
      notation?: 'standard' | 'scientific' | 'engineering' | 'compact';
    }

    interface CurrencyFormatOptions {
      locale?: string;
      currencyDisplay?: 'symbol' | 'code' | 'name';
      minimumFractionDigits?: number;
      maximumFractionDigits?: number;
    }

    interface RGB {
      r: number;
      g: number;
      b: number;
    }

    interface HSL {
      h: number;
      s: number;
      l: number;
    }
  }

  // Storage namespace
  namespace Storage {
    interface StorageService {
      get: <T>(key: string) => Promise<T | null>;
      set: <T>(key: string, value: T, ttl?: number) => Promise<void>;
      remove: (key: string) => Promise<void>;
      clear: () => Promise<void>;
      keys: () => Promise<string[]>;
      has: (key: string) => Promise<boolean>;
      size: () => Promise<number>;
    }

    interface LocalStorageService extends StorageService {
      getSync: <T>(key: string) => T | null;
      setSync: <T>(key: string, value: T) => void;
      removeSync: (key: string) => void;
      clearSync: () => void;
      keysSync: () => string[];
      hasSync: (key: string) => boolean;
      sizeSync: () => number;
    }

    interface SessionStorageService extends StorageService {
      getSync: <T>(key: string) => T | null;
      setSync: <T>(key: string, value: T) => void;
      removeSync: (key: string) => void;
      clearSync: () => void;
      keysSync: () => string[];
      hasSync: (key: string) => boolean;
      sizeSync: () => number;
    }

    interface IndexedDBService extends StorageService {
      createStore: (name: string, options?: StoreOptions) => Promise<void>;
      deleteStore: (name: string) => Promise<void>;
      getStores: () => Promise<string[]>;
      transaction: <T>(stores: string[], mode: 'readonly' | 'readwrite', callback: (tx: Transaction) => Promise<T>) => Promise<T>;
    }

    interface StoreOptions {
      keyPath?: string;
      autoIncrement?: boolean;
      indexes?: IndexDefinition[];
    }

    interface IndexDefinition {
      name: string;
      keyPath: string;
      unique?: boolean;
      multiEntry?: boolean;
    }

    interface Transaction {
      objectStore: (name: string) => ObjectStore;
      complete: () => Promise<void>;
      abort: () => void;
    }

    interface ObjectStore {
      add: (value: any, key?: any) => Promise<any>;
      put: (value: any, key?: any) => Promise<any>;
      get: (key: any) => Promise<any>;
      delete: (key: any) => Promise<void>;
      clear: () => Promise<void>;
      count: () => Promise<number>;
      getAll: () => Promise<any[]>;
      getAllKeys: () => Promise<any[]>;
      index: (name: string) => Index;
    }

    interface Index {
      get: (key: any) => Promise<any>;
      getAll: (query?: any, count?: number) => Promise<any[]>;
      getAllKeys: (query?: any, count?: number) => Promise<any[]>;
      count: (query?: any) => Promise<number>;
    }
  }

  // Configuration namespace
  namespace Configuration {
    interface ConfigurationService {
      get: <T>(key: string, defaultValue?: T) => T;
      set: <T>(key: string, value: T) => void;
      has: (key: string) => boolean;
      remove: (key: string) => void;
      clear: () => void;
      keys: () => string[];
      values: () => any[];
      entries: () => [string, any][];
      merge: (config: Record<string, any>) => void;
      load: (source: ConfigurationSource) => Promise<void>;
      save: (target: ConfigurationTarget) => Promise<void>;
      watch: (key: string, callback: (value: any, oldValue: any) => void) => () => void;
      validate: (schema: ConfigurationSchema) => ValidationResult;
    }

    interface EnvironmentService {
      get: (key: string, defaultValue?: string) => string;
      has: (key: string) => boolean;
      isDevelopment: () => boolean;
      isProduction: () => boolean;
      isTest: () => boolean;
      getNodeEnv: () => string;
      getApiUrl: () => string;
      getFeatureFlags: () => Record<string, boolean>;
    }

    interface FeatureFlagService {
      isEnabled: (flag: string, context?: FlagContext) => boolean;
      getFlag: (flag: string, context?: FlagContext) => FlagValue;
      getAllFlags: (context?: FlagContext) => Record<string, FlagValue>;
      updateFlag: (flag: string, value: FlagValue) => void;
      deleteFlag: (flag: string) => void;
      refresh: () => Promise<void>;
      subscribe: (callback: (flags: Record<string, FlagValue>) => void) => () => void;
    }

    // Configuration Models
    interface ConfigurationSource {
      type: 'file' | 'env' | 'remote' | 'memory';
      location?: string;
      options?: Record<string, any>;
    }

    interface ConfigurationTarget {
      type: 'file' | 'env' | 'remote' | 'memory';
      location?: string;
      options?: Record<string, any>;
    }

    interface ConfigurationSchema {
      [key: string]: ConfigurationProperty;
    }

    interface ConfigurationProperty {
      type: 'string' | 'number' | 'boolean' | 'array' | 'object';
      required?: boolean;
      default?: any;
      enum?: any[];
      pattern?: string;
      minimum?: number;
      maximum?: number;
      properties?: ConfigurationSchema;
      items?: ConfigurationProperty;
    }

    interface FlagContext {
      userId?: string;
      tenantId?: string;
      environment?: string;
      version?: string;
      metadata?: Record<string, any>;
    }

    interface FlagValue {
      enabled: boolean;
      value?: any;
      metadata?: Record<string, any>;
    }
  }
}

// Export the namespace for external use
export { SharedUtilities };

// Export base types for convenience
export type {
  BaseUtilityProps,
  ConfigurationOptions,
  ErrorContext
};