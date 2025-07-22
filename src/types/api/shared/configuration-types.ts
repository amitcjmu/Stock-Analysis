/**
 * Configuration Types
 * 
 * Common configuration structures used across API types.
 */

// Base configuration interface
export interface BaseConfiguration {
  enabled: boolean;
  name?: string;
  description?: string;
  version?: string;
}

// Database configuration
export interface DatabaseConfiguration extends BaseConfiguration {
  host: string;
  port: number;
  database: string;
  username?: string;
  password?: string;
  ssl?: boolean;
  poolSize?: number;
  connectionTimeout?: number;
  queryTimeout?: number;
  options?: Record<string, string | number | boolean>;
}

// Storage configuration
export interface StorageConfiguration extends BaseConfiguration {
  type: 'local' | 's3' | 'azure' | 'gcs' | 'custom';
  endpoint?: string;
  bucket?: string;
  region?: string;
  accessKey?: string;
  secretKey?: string;
  prefix?: string;
  retentionDays?: number;
  compressionEnabled?: boolean;
  encryptionEnabled?: boolean;
}

// Logging configuration
export interface LoggingConfiguration extends BaseConfiguration {
  level: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
  format: 'json' | 'text' | 'structured';
  outputs: Array<{
    type: 'console' | 'file' | 'remote';
    target?: string;
    format?: string;
    level?: string;
  }>;
  retention?: {
    days: number;
    maxSize?: string;
    maxFiles?: number;
  };
  sampling?: {
    enabled: boolean;
    rate: number;
  };
}

// Processing configuration
export interface ProcessingConfiguration extends BaseConfiguration {
  batchSize: number;
  parallelism: number;
  timeout: number;
  retryPolicy: {
    maxRetries: number;
    backoffMultiplier: number;
    initialDelay: number;
    maxDelay: number;
  };
  resourceLimits?: {
    maxMemory?: string;
    maxCpu?: number;
    maxDiskUsage?: string;
  };
}

// API configuration
export interface ApiConfiguration extends BaseConfiguration {
  baseUrl: string;
  timeout: number;
  retries: number;
  headers?: Record<string, string>;
  authentication?: {
    type: 'none' | 'basic' | 'bearer' | 'oauth2' | 'apikey';
    credentials?: Record<string, string>;
  };
  rateLimit?: {
    requestsPerSecond: number;
    burst: number;
  };
}

// Notification configuration
export interface NotificationConfiguration extends BaseConfiguration {
  channels: Array<{
    type: 'email' | 'sms' | 'webhook' | 'slack' | 'teams';
    enabled: boolean;
    config: Record<string, string | number | boolean>;
  }>;
  templates?: Record<string, {
    subject?: string;
    body: string;
    format: 'text' | 'html' | 'markdown';
  }>;
  rules?: Array<{
    event: string;
    channels: string[];
    conditions?: Record<string, string | number | boolean>;
  }>;
}

// Security configuration
export interface SecurityConfiguration extends BaseConfiguration {
  encryption: {
    algorithm: string;
    keyRotationDays: number;
  };
  authentication: {
    methods: string[];
    sessionTimeout: number;
    mfaRequired: boolean;
  };
  authorization: {
    model: 'rbac' | 'abac' | 'custom';
    cacheTimeout: number;
  };
  audit: {
    enabled: boolean;
    events: string[];
    retention: number;
  };
}

// Generic configuration for flexibility
export type GenericConfiguration = BaseConfiguration & Record<string, string | number | boolean | Record<string, string | number | boolean>>;