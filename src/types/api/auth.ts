/**
 * Authentication API Types
 * 
 * Type definitions for Authentication and Authorization APIs including
 * login, logout, token management, session handling, and security operations.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from './shared';

// Authentication APIs
export interface LoginRequest extends BaseApiRequest {
  email: string;
  password: string;
  remember?: boolean;
  mfaToken?: string;
  deviceId?: string;
  deviceName?: string;
  ipAddress?: string;
  userAgent?: string;
}

export interface LoginResponse extends BaseApiResponse<AuthenticationResult> {
  data: AuthenticationResult;
  sessionId: string;
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
  user: AuthenticatedUser;
  permissions: string[];
  mfaRequired?: boolean;
  mfaChallenge?: MFAChallenge;
}

export interface LogoutRequest extends BaseApiRequest {
  sessionId?: string;
  revokeAllSessions?: boolean;
  context: MultiTenantContext;
}

export interface LogoutResponse extends BaseApiResponse<LogoutResult> {
  data: LogoutResult;
  loggedOutAt: string;
  sessionsRevoked: number;
  tokensRevoked: number;
}

export interface RefreshTokenRequest extends BaseApiRequest {
  refreshToken: string;
  deviceId?: string;
  ipAddress?: string;
  userAgent?: string;
}

export interface RefreshTokenResponse extends BaseApiResponse<TokenRefreshResult> {
  data: TokenRefreshResult;
  accessToken: string;
  refreshToken?: string;
  expiresAt: string;
  tokenType: string;
}

export interface ForgotPasswordRequest extends BaseApiRequest {
  email: string;
  resetUrl?: string;
  language?: string;
}

export interface ForgotPasswordResponse extends BaseApiResponse<PasswordResetResult> {
  data: PasswordResetResult;
  resetTokenSent: boolean;
  expiresAt: string;
  deliveryMethod: 'email' | 'sms';
}

export interface ResetPasswordRequest extends BaseApiRequest {
  resetToken: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ResetPasswordResponse extends BaseApiResponse<PasswordChangeResult> {
  data: PasswordChangeResult;
  passwordChanged: boolean;
  loginRequired: boolean;
  sessionInvalidated: boolean;
}

export interface ChangePasswordRequest extends BaseApiRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
  invalidateOtherSessions?: boolean;
  context: MultiTenantContext;
}

export interface ChangePasswordResponse extends BaseApiResponse<PasswordChangeResult> {
  data: PasswordChangeResult;
  passwordChanged: boolean;
  strengthScore: number;
  sessionsInvalidated: number;
}

// Multi-Factor Authentication APIs
export interface SetupMFARequest extends BaseApiRequest {
  method: MFAMethod;
  phoneNumber?: string;
  backupCodes?: boolean;
  context: MultiTenantContext;
}

export interface SetupMFAResponse extends BaseApiResponse<MFASetupResult> {
  data: MFASetupResult;
  setupId: string;
  qrCode?: string;
  secret?: string;
  backupCodes?: string[];
  verificationRequired: boolean;
}

export interface VerifyMFASetupRequest extends BaseApiRequest {
  setupId: string;
  verificationCode: string;
  context: MultiTenantContext;
}

export interface VerifyMFASetupResponse extends BaseApiResponse<MFAVerificationResult> {
  data: MFAVerificationResult;
  verified: boolean;
  mfaEnabled: boolean;
  backupCodes: string[];
  recoveryCodes: string[];
}

export interface DisableMFARequest extends BaseApiRequest {
  password: string;
  verificationCode?: string;
  reason?: string;
  context: MultiTenantContext;
}

export interface DisableMFAResponse extends BaseApiResponse<MFADisableResult> {
  data: MFADisableResult;
  disabled: boolean;
  disabledAt: string;
  backupMethodsRevoked: boolean;
}

export interface VerifyMFARequest extends BaseApiRequest {
  sessionId: string;
  verificationCode: string;
  method: MFAMethod;
  trustDevice?: boolean;
}

export interface VerifyMFAResponse extends BaseApiResponse<MFAVerificationResult> {
  data: MFAVerificationResult;
  verified: boolean;
  accessToken?: string;
  sessionUpdated: boolean;
  deviceTrusted: boolean;
}

export interface GenerateBackupCodesRequest extends BaseApiRequest {
  password: string;
  invalidateExisting?: boolean;
  context: MultiTenantContext;
}

export interface GenerateBackupCodesResponse extends BaseApiResponse<BackupCodesResult> {
  data: BackupCodesResult;
  backupCodes: string[];
  generatedAt: string;
  expiresAt?: string;
  previousCodesInvalidated: boolean;
}

// Session Management APIs
export interface GetSessionsRequest extends BaseApiRequest {
  userId?: string;
  active?: boolean;
  deviceType?: string;
  includeExpired?: boolean;
  context: MultiTenantContext;
}

export interface GetSessionsResponse extends BaseApiResponse<UserSession[]> {
  data: UserSession[];
  activeSessions: number;
  expiredSessions: number;
  currentSession: string;
}

export interface GetSessionDetailsRequest extends BaseApiRequest {
  sessionId: string;
  includeActivity?: boolean;
  includeDevice?: boolean;
  includeLocation?: boolean;
  context: MultiTenantContext;
}

export interface GetSessionDetailsResponse extends BaseApiResponse<SessionDetails> {
  data: SessionDetails;
  activity: SessionActivity[];
  device: DeviceInfo;
  location: LocationInfo;
  security: SessionSecurity;
}

export interface RevokeSessionRequest extends BaseApiRequest {
  sessionId: string;
  reason?: string;
  notifyUser?: boolean;
  context: MultiTenantContext;
}

export interface RevokeSessionResponse extends BaseApiResponse<SessionRevocationResult> {
  data: SessionRevocationResult;
  revokedAt: string;
  tokensInvalidated: number;
  userNotified: boolean;
}

export interface RevokeAllSessionsRequest extends BaseApiRequest {
  userId?: string;
  excludeCurrent?: boolean;
  reason?: string;
  notifyUser?: boolean;
  context: MultiTenantContext;
}

export interface RevokeAllSessionsResponse extends BaseApiResponse<BulkSessionRevocationResult> {
  data: BulkSessionRevocationResult;
  sessionsRevoked: number;
  tokensInvalidated: number;
  currentSessionPreserved: boolean;
  userNotified: boolean;
}

// Authorization APIs
export interface CheckPermissionRequest extends BaseApiRequest {
  permission: string;
  resource?: string;
  resourceId?: string;
  action?: string;
  context: MultiTenantContext;
}

export interface CheckPermissionResponse extends BaseApiResponse<PermissionCheckResult> {
  data: PermissionCheckResult;
  allowed: boolean;
  reason?: string;
  conditions?: PermissionCondition[];
  expires?: string;
}

export interface CheckMultiplePermissionsRequest extends BaseApiRequest {
  permissions: PermissionCheck[];
  context: MultiTenantContext;
}

export interface CheckMultiplePermissionsResponse extends BaseApiResponse<PermissionCheckResult[]> {
  data: PermissionCheckResult[];
  summary: PermissionSummary;
}

export interface GetUserPermissionsRequest extends BaseApiRequest {
  userId?: string;
  includeInherited?: boolean;
  includeExpired?: boolean;
  resource?: string;
  context: MultiTenantContext;
}

export interface GetUserPermissionsResponse extends BaseApiResponse<UserPermissions> {
  data: UserPermissions;
  directPermissions: Permission[];
  inheritedPermissions: Permission[];
  effectivePermissions: string[];
  restrictions: PermissionRestriction[];
}

export interface GrantPermissionRequest extends BaseApiRequest {
  userId: string;
  permission: string;
  resource?: string;
  resourceId?: string;
  scope?: PermissionScope;
  expiresAt?: string;
  conditions?: PermissionCondition[];
  context: MultiTenantContext;
}

export interface GrantPermissionResponse extends BaseApiResponse<PermissionGrant> {
  data: PermissionGrant;
  grantId: string;
  grantedAt: string;
  effectivePermissions: string[];
  notificationSent: boolean;
}

export interface RevokePermissionRequest extends BaseApiRequest {
  userId: string;
  permission: string;
  resource?: string;
  resourceId?: string;
  reason?: string;
  notifyUser?: boolean;
  context: MultiTenantContext;
}

export interface RevokePermissionResponse extends BaseApiResponse<PermissionRevocation> {
  data: PermissionRevocation;
  revokedAt: string;
  remainingPermissions: string[];
  userNotified: boolean;
}

// Token Management APIs
export interface CreateApiTokenRequest extends BaseApiRequest {
  name: string;
  description?: string;
  permissions: string[];
  expiresAt?: string;
  scope?: TokenScope;
  rateLimit?: RateLimit;
  context: MultiTenantContext;
}

export interface CreateApiTokenResponse extends BaseApiResponse<ApiToken> {
  data: ApiToken;
  tokenId: string;
  token: string;
  createdAt: string;
  permissions: string[];
  restrictions: TokenRestriction[];
}

export interface GetApiTokensRequest extends BaseApiRequest {
  userId?: string;
  active?: boolean;
  includeExpired?: boolean;
  includeRevoked?: boolean;
  context: MultiTenantContext;
}

export interface GetApiTokensResponse extends BaseApiResponse<ApiTokenSummary[]> {
  data: ApiTokenSummary[];
  activeTokens: number;
  expiredTokens: number;
  revokedTokens: number;
}

export interface RevokeApiTokenRequest extends BaseApiRequest {
  tokenId: string;
  reason?: string;
  notifyUser?: boolean;
  context: MultiTenantContext;
}

export interface RevokeApiTokenResponse extends BaseApiResponse<TokenRevocationResult> {
  data: TokenRevocationResult;
  revokedAt: string;
  userNotified: boolean;
}

export interface ValidateTokenRequest extends BaseApiRequest {
  token: string;
  permission?: string;
  resource?: string;
  action?: string;
}

export interface ValidateTokenResponse extends BaseApiResponse<TokenValidationResult> {
  data: TokenValidationResult;
  valid: boolean;
  user: TokenUser;
  permissions: string[];
  expires: string;
  rateLimit: RateLimitStatus;
}

// Security APIs
export interface GetSecuritySettingsRequest extends BaseApiRequest {
  userId?: string;
  includeDefaults?: boolean;
  context: MultiTenantContext;
}

export interface GetSecuritySettingsResponse extends BaseApiResponse<SecuritySettings> {
  data: SecuritySettings;
  passwordPolicy: PasswordPolicy;
  sessionPolicy: SessionPolicy;
  mfaPolicy: MFAPolicy;
  loginAttempts: LoginAttemptInfo;
}

export interface UpdateSecuritySettingsRequest extends BaseApiRequest {
  settings: Partial<SecuritySettingsData>;
  validateChanges?: boolean;
  notifyUser?: boolean;
  context: MultiTenantContext;
}

export interface UpdateSecuritySettingsResponse extends BaseApiResponse<SecuritySettings> {
  data: SecuritySettings;
  changesApplied: SecurityChange[];
  validationResults: SecurityValidationResult[];
  userNotified: boolean;
}

export interface GetLoginHistoryRequest extends BaseApiRequest {
  userId?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  successful?: boolean;
  includeDetails?: boolean;
  limit?: number;
  context: MultiTenantContext;
}

export interface GetLoginHistoryResponse extends BaseApiResponse<LoginAttempt[]> {
  data: LoginAttempt[];
  summary: LoginSummary;
  securityEvents: SecurityEvent[];
  riskIndicators: RiskIndicator[];
}

export interface ReportSecurityIncidentRequest extends BaseApiRequest {
  incidentType: SecurityIncidentType;
  severity: SecuritySeverity;
  description: string;
  evidence?: string[];
  affectedResources?: string[];
  suspectedUsers?: string[];
  context: MultiTenantContext;
}

export interface ReportSecurityIncidentResponse extends BaseApiResponse<SecurityIncident> {
  data: SecurityIncident;
  incidentId: string;
  reportedAt: string;
  assignedTo?: string;
  ticketNumber?: string;
  investigationStarted: boolean;
}

// Supporting Data Types
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
  metadata: Record<string, any>;
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
  attributes?: Record<string, any>;
}

export interface PermissionCondition {
  type: string;
  operator: string;
  value: any;
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

export type MFAMethod = 'totp' | 'sms' | 'email' | 'backup_code' | 'hardware_token';
export type SessionStatus = 'active' | 'expired' | 'revoked' | 'locked';
export type TokenStatus = 'active' | 'expired' | 'revoked' | 'suspended';
export type SecurityIncidentType = 'unauthorized_access' | 'data_breach' | 'malware' | 'phishing' | 'policy_violation' | 'suspicious_activity';
export type SecuritySeverity = 'low' | 'medium' | 'high' | 'critical';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)