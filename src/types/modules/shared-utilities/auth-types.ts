/**
 * Authentication & Authorization Types
 *
 * Types for authentication, authorization, multi-tenancy, and session management.
 */

// Authentication service interfaces
export interface AuthenticationService {
  login: (credentials: LoginCredentials) => Promise<AuthResult>;
  logout: () => Promise<void>;
  refreshToken: (token: string) => Promise<AuthResult>;
  validateToken: (token: string) => Promise<TokenValidation>;
  getCurrentUser: () => Promise<User>;
  updateProfile: (updates: Partial<UserProfile>) => Promise<UserProfile>;
  changePassword: (request: PasswordChangeRequest) => Promise<void>;
  resetPassword: (request: PasswordResetRequest) => Promise<void>;
}

export interface AuthorizationService {
  hasPermission: (permission: string, context?: AuthContext) => boolean;
  hasRole: (role: string, context?: AuthContext) => boolean;
  canAccess: (resource: string, action: string, context?: AuthContext) => boolean;
  getPermissions: (userId: string, context?: AuthContext) => Promise<Permission[]>;
  getRoles: (userId: string, context?: AuthContext) => Promise<Role[]>;
  checkResourceAccess: (resourceId: string, action: string) => Promise<boolean>;
}

export interface MultiTenantService {
  getCurrentTenant: () => Promise<Tenant>;
  switchTenant: (tenantId: string) => Promise<void>;
  getTenantContext: () => TenantContext;
  validateTenantAccess: (tenantId: string) => Promise<boolean>;
  getTenantSettings: (tenantId: string) => Promise<TenantSettings>;
  updateTenantSettings: (tenantId: string, updates: Partial<TenantSettings>) => Promise<void>;
}

export interface SessionService {
  createSession: (userId: string, metadata?: Record<string, unknown>) => Promise<Session>;
  getSession: (sessionId: string) => Promise<Session>;
  updateSession: (sessionId: string, updates: Partial<Session>) => Promise<void>;
  destroySession: (sessionId: string) => Promise<void>;
  validateSession: (sessionId: string) => Promise<SessionValidation>;
  extendSession: (sessionId: string, duration: number) => Promise<void>;
}

// Auth model types
export interface LoginCredentials {
  username: string;
  password: string;
  tenantId?: string;
  mfaCode?: string;
  rememberMe?: boolean;
}

export interface AuthResult {
  success: boolean;
  user: User;
  tokens: AuthTokens;
  permissions: Permission[];
  roles: Role[];
  tenantContext: TenantContext;
  expiresAt: string;
}

export interface TokenValidation {
  isValid: boolean;
  user?: User;
  permissions?: Permission[];
  roles?: Role[];
  expiresAt?: string;
  error?: string;
}

export interface User {
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

export interface UserProfile {
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

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
  scope: string;
}

export interface Permission {
  id: string;
  name: string;
  description: string;
  resource: string;
  actions: string[];
  conditions?: PermissionCondition[];
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
  inherits: string[];
  context: 'global' | 'tenant' | 'engagement';
}

export interface AuthContext {
  tenantId?: string;
  engagementId?: string;
  resourceId?: string;
  metadata?: Record<string, unknown>;
}

export interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  status: 'active' | 'inactive' | 'suspended';
  settings: TenantSettings;
  limits: TenantLimits;
  createdAt: string;
  updatedAt: string;
}

export interface TenantContext {
  tenantId: string;
  tenantName: string;
  engagementId?: string;
  userId: string;
  permissions: Permission[];
  roles: Role[];
  settings: TenantSettings;
}

export interface TenantSettings {
  branding: BrandingSettings;
  security: SecuritySettings;
  features: FeatureSettings;
  integrations: IntegrationSettings;
  notifications: NotificationSettings;
}

export interface Session {
  id: string;
  userId: string;
  tenantId: string;
  status: 'active' | 'expired' | 'terminated';
  createdAt: string;
  lastAccessAt: string;
  expiresAt: string;
  ipAddress: string;
  userAgent: string;
  metadata: Record<string, unknown>;
}

export interface SessionValidation {
  isValid: boolean;
  session?: Session;
  user?: User;
  tenant?: Tenant;
  error?: string;
}

export interface PasswordChangeRequest {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface PasswordResetRequest {
  email: string;
  token?: string;
  newPassword?: string;
}

export interface PermissionCondition {
  field: string;
  operator: 'eq' | 'ne' | 'in' | 'not_in' | 'gt' | 'lt' | 'gte' | 'lte';
  value: string | number | boolean | string[] | number[];
}

export interface TenantLimits {
  maxUsers: number;
  maxEngagements: number;
  maxFlows: number;
  maxStorage: number;
  maxApiCalls: number;
}

export interface BrandingSettings {
  logo?: string;
  favicon?: string;
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  customCSS?: string;
}

export interface SecuritySettings {
  passwordPolicy: PasswordPolicy;
  sessionTimeout: number;
  mfaRequired: boolean;
  mfaMethods: string[];
  ipWhitelist: string[];
  auditLogging: boolean;
}

export interface FeatureSettings {
  enabledFeatures: string[];
  disabledFeatures: string[];
  betaFeatures: string[];
  limits: Record<string, number>;
}

export interface IntegrationSettings {
  enabledIntegrations: string[];
  configurations: Record<string, unknown>;
  webhooks: WebhookConfig[];
}

export interface NotificationSettings {
  emailEnabled: boolean;
  smsEnabled: boolean;
  pushEnabled: boolean;
  channels: NotificationChannel[];
  preferences: NotificationPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  dateFormat: string;
  timeFormat: string;
  numberFormat: string;
  pageSize: number;
  autoSave: boolean;
  shortcuts: Record<string, string>;
}

export interface PasswordPolicy {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  maxAge: number;
  historySize: number;
}

export interface WebhookConfig {
  id: string;
  name: string;
  url: string;
  events: string[];
  headers: Record<string, string>;
  secret: string;
  active: boolean;
}

export interface NotificationChannel {
  id: string;
  type: 'email' | 'sms' | 'push' | 'slack' | 'webhook';
  name: string;
  configuration: Record<string, unknown>;
  enabled: boolean;
}

export interface NotificationPreferences {
  email: boolean;
  sms: boolean;
  push: boolean;
  frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  categories: Record<string, boolean>;
}
