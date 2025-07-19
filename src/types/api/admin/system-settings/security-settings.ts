/**
 * Security Settings Configuration Types
 * 
 * Security-related configuration including authentication, authorization,
 * encryption, session management, and security monitoring.
 * 
 * Generated with CC for modular admin type organization.
 */

// Security Settings Configuration
export interface SecuritySettings {
  authentication: AuthenticationConfig;
  authorization: AuthorizationConfig;
  encryption: EncryptionConfig;
  session: SessionConfig;
  audit: AuditConfig;
  rateLimit: RateLimitConfig;
  cors: CorsConfig;
  csrf: CsrfConfig;
  headers: SecurityHeadersConfig;
  mfa: MfaConfig;
}

export interface AuthenticationConfig {
  methods: string[];
  sessionTimeout: number;
  maxAttempts: number;
  lockoutDuration: number;
}

export interface AuthorizationConfig {
  rbacEnabled: boolean;
  defaultRole: string;
  hierarchicalRoles: boolean;
}

export interface EncryptionConfig {
  algorithm: string;
  keySize: number;
  rotationInterval: number;
}

export interface SessionConfig {
  timeout: number;
  sliding: boolean;
  sameSite: string;
}

export interface AuditConfig {
  enabled: boolean;
  level: string;
  retention: number;
}

export interface RateLimitConfig {
  enabled: boolean;
  requests: number;
  window: number;
}

export interface CorsConfig {
  enabled: boolean;
  origins: string[];
  methods: string[];
}

export interface CsrfConfig {
  enabled: boolean;
  sameSite: string;
  secure: boolean;
}

export interface SecurityHeadersConfig {
  hsts: boolean;
  xssProtection: boolean;
  contentTypeOptions: boolean;
}

export interface MfaConfig {
  required: boolean;
  methods: string[];
  gracePeriod: number;
}