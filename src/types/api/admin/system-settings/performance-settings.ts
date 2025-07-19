/**
 * Performance Settings Configuration Types
 * 
 * Performance optimization configuration including caching, compression,
 * CDN, database performance, and scaling settings.
 * 
 * Generated with CC for modular admin type organization.
 */

// Performance Settings Configuration
export interface PerformanceSettings {
  caching: CachingConfig;
  compression: CompressionConfig;
  cdn: CdnConfig;
  database: DatabasePerformanceConfig;
  api: ApiPerformanceConfig;
  background: BackgroundJobConfig;
  scaling: ScalingConfig;
  optimization: OptimizationConfig;
}

export interface CachingConfig {
  enabled: boolean;
  provider: string;
  ttl: number;
}

export interface CompressionConfig {
  enabled: boolean;
  algorithm: string;
  level: number;
}

export interface CdnConfig {
  enabled: boolean;
  provider: string;
  domains: string[];
}

export interface DatabasePerformanceConfig {
  poolSize: number;
  timeout: number;
  slowQueryThreshold: number;
}

export interface ApiPerformanceConfig {
  rateLimit: number;
  timeout: number;
  caching: boolean;
}

export interface BackgroundJobConfig {
  enabled: boolean;
  maxConcurrency: number;
  retries: number;
}

export interface ScalingConfig {
  autoScaling: boolean;
  minInstances: number;
  maxInstances: number;
}

export interface OptimizationConfig {
  enabled: boolean;
  strategies: string[];
  threshold: number;
}