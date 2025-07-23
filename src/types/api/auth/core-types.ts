/**
 * Core Authentication and Authorization Types
 * 
 * Shared interfaces and types used across authentication modules.
 */

import type { ActivityMetadata, PermissionMetadata } from '../shared/metadata-types';
import type { ConditionValue, PrimitiveValue } from '../shared/value-types';

// Core Authentication Types
export interface AuthenticationResult {
  authenticated: boolean;
  user: AuthenticatedUser;
  session: SessionInfo;
  tokens: TokenInfo;
  permissions: string[];
  mfaRequired: boolean;
  passwordExpired: boolean;
  accountLocked: boolean;
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  roles: string[];
  clientAccountId?: string;
  engagements: string[];
  preferences: UserPreferences;
  security: UserSecurityInfo;
  lastLoginAt?: string;
}

export interface SessionInfo {
  sessionId: string;
  userId: string;
  deviceId: string;
  deviceName?: string;
  ipAddress: string;
  userAgent: string;
  location?: LocationInfo;
  startedAt: string;
  lastActivityAt: string;
  expiresAt: string;
  trusted: boolean;
}

export interface TokenInfo {
  accessToken: string;
  refreshToken?: string;
  tokenType: string;
  expiresIn: number;
  scope: string[];
  audience: string;
  issuer: string;
}

export interface MFAChallenge {
  challengeId: string;
  method: MFAMethod;
  deliveryTarget?: string;
  expiresAt: string;
  attemptsRemaining: number;
}

export interface UserSession {
  sessionId: string;
  deviceId: string;
  deviceName?: string;
  deviceType: string;
  platform: string;
  browser?: string;
  ipAddress: string;
  location?: LocationInfo;
  current: boolean;
  trusted: boolean;
  startedAt: string;
  lastActivityAt: string;
  expiresAt: string;
  status: SessionStatus;
}

export interface SessionDetails {
  session: UserSession;
  activity: SessionActivity[];
  device: DeviceInfo;
  location: LocationInfo;
  security: SessionSecurity;
  permissions: string[];
  riskScore: number;
}

export interface SessionActivity {
  timestamp: string;
  action: string;
  resource: string;
  ipAddress: string;
  userAgent: string;
  success: boolean;
  riskScore: number;
  metadata: ActivityMetadata;
}

export interface DeviceInfo {
  deviceId: string;
  deviceName?: string;
  deviceType: 'desktop' | 'mobile' | 'tablet' | 'unknown';
  platform: string;
  browser?: string;
  os: string;
  trusted: boolean;
  firstSeen: string;
  lastSeen: string;
  fingerprint: string;
}

export interface LocationInfo {
  country?: string;
  region?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  timezone?: string;
  isp?: string;
  suspicious: boolean;
}

export interface SessionSecurity {
  encrypted: boolean;
  mfaVerified: boolean;
  riskScore: number;
  threats: ThreatInfo[];
  anomalies: AnomalyInfo[];
  lastSecurityCheck: string;
}

export interface Permission {
  id: string;
  name: string;
  description?: string;
  resource: string;
  action: string;
  scope?: PermissionScope;
  conditions?: PermissionCondition[];
  grantedAt: string;
  grantedBy: string;
  expiresAt?: string;
}

export interface PermissionScope {
  clientAccountId?: string;
  engagementId?: string;
  resourceId?: string;
  attributes?: PermissionMetadata;
}

export interface PermissionCondition {
  type: string;
  operator: string;
  value: ConditionValue;
  description?: string;
}

export interface ApiToken {
  id: string;
  name: string;
  description?: string;
  userId: string;
  permissions: string[];
  scope: TokenScope;
  status: TokenStatus;
  createdAt: string;
  expiresAt?: string;
  lastUsedAt?: string;
  rateLimit?: RateLimit;
  restrictions: TokenRestriction[];
}

export interface TokenScope {
  clientAccountId?: string;
  engagementId?: string;
  resources?: string[];
  actions?: string[];
}

export interface RateLimit {
  requests: number;
  window: number;
  burst?: number;
}

export interface SecuritySettings {
  passwordPolicy: PasswordPolicy;
  sessionPolicy: SessionPolicy;
  mfaPolicy: MFAPolicy;
  loginPolicy: LoginPolicy;
  devicePolicy: DevicePolicy;
  auditPolicy: AuditPolicy;
}

export interface PasswordPolicy {
  minLength: number;
  maxLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  preventCommonPasswords: boolean;
  preventPasswordReuse: number;
  maxAge: number;
  warningDays: number;
}

export interface SessionPolicy {
  maxSessions: number;
  idleTimeout: number;
  absoluteTimeout: number;
  extendOnActivity: boolean;
  requireMfaForSensitive: boolean;
  allowConcurrentSessions: boolean;
  forceLogoutOnRoleChange: boolean;
}

export interface MFAPolicy {
  required: boolean;
  methods: MFAMethod[];
  gracePeriod: number;
  backupCodesEnabled: boolean;
  trustedDevices: boolean;
  trustedDeviceDuration: number;
}

export interface LoginPolicy {
  maxFailedAttempts: number;
  lockoutDuration: number;
  progressiveLockout: boolean;
  requireMfaAfterLockout: boolean;
  allowedIpRanges?: string[];
  deniedIpRanges?: string[];
  allowUnknownDevices: boolean;
}

// Type Aliases
export type MFAMethod = 'totp' | 'sms' | 'email' | 'backup_code' | 'hardware_token';
export type SessionStatus = 'active' | 'expired' | 'revoked' | 'locked';
export type TokenStatus = 'active' | 'expired' | 'revoked' | 'suspended';
export type SecurityIncidentType = 'unauthorized_access' | 'data_breach' | 'malware' | 'phishing' | 'policy_violation' | 'suspicious_activity';
export type SecuritySeverity = 'low' | 'medium' | 'high' | 'critical';

// Result Types
export interface LogoutResult {
  loggedOut: boolean;
  sessionId: string;
  loggedOutAt: string;
  tokensRevoked: number;
}

export interface PasswordChangeResult {
  changed: boolean;
  strengthScore: number;
  changedAt: string;
  requiresReauth: boolean;
}

export interface TokenRefreshResult {
  refreshed: boolean;
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
  tokenType: string;
}

export interface PasswordResetResult {
  resetInitiated: boolean;
  deliveryMethod: 'email' | 'sms';
  expiresAt: string;
}

export interface MFASetupResult {
  setupComplete: boolean;
  method: MFAMethod;
  verificationRequired: boolean;
  backupCodes?: string[];
}

export interface MFAVerificationResult {
  verified: boolean;
  sessionId?: string;
  accessToken?: string;
  deviceTrusted: boolean;
}

export interface MFADisableResult {
  disabled: boolean;
  disabledAt: string;
  backupMethodsRevoked: boolean;
}

export interface BackupCodesResult {
  generated: boolean;
  codes: string[];
  generatedAt: string;
  expiresAt?: string;
}

export interface TokenValidationResult {
  valid: boolean;
  user: TokenUser;
  permissions: string[];
  expires: string;
  scope: string[];
}

export interface TokenUser {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

export interface UserPermissions {
  userId: string;
  permissions: Permission[];
  roles: Role[];
  effectivePermissions: string[];
}

export interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  clientAccountId?: string;
  engagementId?: string;
}

export interface ResourceAccess {
  resourceType: string;
  resourceId: string;
  permissions: string[];
  accessLevel: string;
}

// Additional supporting interfaces
export interface UserPreferences {
  language: string;
  timezone: string;
  dateFormat: string;
  theme: string;
  notifications: NotificationPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  loginAlerts: boolean;
  securityAlerts: boolean;
}

export interface UserSecurityInfo {
  mfaEnabled: boolean;
  mfaMethods: MFAMethod[];
  lastPasswordChange: string;
  loginAttempts: number;
  accountLocked: boolean;
  lockoutUntil?: string;
  trustedDevices: string[];
}

export interface ThreatInfo {
  type: string;
  severity: SecuritySeverity;
  description: string;
  detectedAt: string;
  mitigated: boolean;
}

export interface AnomalyInfo {
  type: string;
  score: number;
  description: string;
  detectedAt: string;
  factors: string[];
}

export interface TokenRestriction {
  type: string;
  value: string;
  description?: string;
}

export interface DevicePolicy {
  requireTrustedDevices: boolean;
  trustDuration: number;
  maxDevices: number;
  allowUnknownDevices: boolean;
  deviceRegistrationRequired: boolean;
}

export interface AuditPolicy {
  enabled: boolean;
  retentionDays: number;
  logLevel: string;
  includeApiCalls: boolean;
  includeDataAccess: boolean;
}

export interface PermissionCheckResult {
  allowed: boolean;
  permission: string;
  resource?: string;
  reason?: string;
  conditions?: PermissionCondition[];
}

export interface PermissionCheck {
  permission: string;
  resource?: string;
  resourceId?: string;
  action?: string;
}

export interface PermissionSummary {
  totalChecks: number;
  allowed: number;
  denied: number;
  conditional: number;
}

export interface PermissionRestriction {
  type: string;
  description: string;
  condition: PermissionCondition;
}

export interface PermissionGrant {
  id: string;
  userId: string;
  permission: string;
  grantedAt: string;
  grantedBy: string;
  expiresAt?: string;
}

export interface PermissionRevocation {
  permissionId: string;
  userId: string;
  revokedAt: string;
  revokedBy: string;
  reason?: string;
}

export interface SessionRevocationResult {
  sessionId: string;
  revoked: boolean;
  revokedAt: string;
  tokensInvalidated: number;
}

export interface BulkSessionRevocationResult {
  sessionsRevoked: number;
  tokensInvalidated: number;
  errors: string[];
}

export interface ApiTokenSummary {
  id: string;
  name: string;
  status: TokenStatus;
  createdAt: string;
  expiresAt?: string;
  lastUsedAt?: string;
  permissions: number;
}

export interface TokenRevocationResult {
  tokenId: string;
  revoked: boolean;
  revokedAt: string;
}

export interface RateLimitStatus {
  remaining: number;
  resetAt: string;
  limit: number;
}

export interface SecuritySettingsData {
  passwordPolicy?: Partial<PasswordPolicy>;
  sessionPolicy?: Partial<SessionPolicy>;
  mfaPolicy?: Partial<MFAPolicy>;
  loginPolicy?: Partial<LoginPolicy>;
}

export interface SecurityChange {
  setting: string;
  oldValue: PrimitiveValue | Record<string, PrimitiveValue>;
  newValue: PrimitiveValue | Record<string, PrimitiveValue>;
  changedAt: string;
}

export interface SecurityValidationResult {
  setting: string;
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface LoginAttempt {
  timestamp: string;
  email: string;
  ipAddress: string;
  userAgent: string;
  success: boolean;
  failureReason?: string;
  deviceId?: string;
  location?: LocationInfo;
  riskScore: number;
}

export interface LoginSummary {
  totalAttempts: number;
  successfulLogins: number;
  failedAttempts: number;
  uniqueIps: number;
  riskEvents: number;
}

export interface SecurityEvent {
  id: string;
  type: string;
  severity: SecuritySeverity;
  timestamp: string;
  description: string;
  userId?: string;
  ipAddress?: string;
  resolved: boolean;
}

export interface RiskIndicator {
  type: string;
  score: number;
  description: string;
  factors: string[];
  mitigated: boolean;
}

export interface SecurityIncident {
  id: string;
  type: SecurityIncidentType;
  severity: SecuritySeverity;
  status: string;
  reportedAt: string;
  assignedTo?: string;
  description: string;
  evidence: string[];
}

export interface LoginAttemptInfo {
  attempts: number;
  lastAttempt?: string;
  lockedUntil?: string;
  successfulLogins: number;
}