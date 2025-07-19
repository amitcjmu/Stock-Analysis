/**
 * User Management API Types
 * 
 * Type definitions for user management operations including user CRUD,
 * user lifecycle management, and user authentication workflows.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ListRequest,
  ListResponse,
  GetRequest,
  GetResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse,
  DeleteRequest,
  DeleteResponse
} from '../shared';

// User Creation APIs
export interface CreateUserRequest extends CreateRequest<UserData> {
  data: UserData;
  sendInvitation?: boolean;
  assignRoles?: string[];
  assignPermissions?: string[];
  requirePasswordChange?: boolean;
}

export interface CreateUserResponse extends CreateResponse<User> {
  data: User;
  userId: string;
  invitationSent: boolean;
  tempPassword?: string;
  activationUrl?: string;
}

// User Retrieval APIs
export interface GetUserRequest extends GetRequest {
  userId: string;
  includeProfile?: boolean;
  includeRoles?: boolean;
  includePermissions?: boolean;
  includeActivity?: boolean;
  includeEngagements?: boolean;
}

export interface GetUserResponse extends GetResponse<User> {
  data: User;
  profile: UserProfile;
  roles: UserRole[];
  permissions: UserPermission[];
  recentActivity: UserActivity[];
  engagements: UserEngagement[];
}

// User Listing APIs
export interface ListUsersRequest extends ListRequest {
  roles?: string[];
  status?: UserStatus[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  lastLoginAfter?: string;
  lastLoginBefore?: string;
  includeInactive?: boolean;
  includeDeleted?: boolean;
}

export interface ListUsersResponse extends ListResponse<UserSummary> {
  data: UserSummary[];
  statistics: UserStatistics;
  roleDistribution: RoleDistribution[];
  activitySummary: ActivitySummary;
}

// User Update APIs
export interface UpdateUserRequest extends UpdateRequest<Partial<UserData>> {
  userId: string;
  data: Partial<UserData>;
  updateType?: 'profile' | 'roles' | 'permissions' | 'status' | 'settings';
  notifyUser?: boolean;
}

export interface UpdateUserResponse extends UpdateResponse<User> {
  data: User;
  changes: UserChange[];
  notifications: UserNotification[];
}

// User Deactivation APIs
export interface DeactivateUserRequest extends BaseApiRequest {
  userId: string;
  reason: string;
  transferOwnership?: boolean;
  newOwnerId?: string;
  retainData?: boolean;
  notifyUser?: boolean;
  context: MultiTenantContext;
}

export interface DeactivateUserResponse extends BaseApiResponse<UserDeactivation> {
  data: UserDeactivation;
  deactivatedAt: string;
  dataTransferred: boolean;
  retainedData: string[];
  notificationSent: boolean;
}

// Supporting Types for User Management
export interface UserData {
  email: string;
  firstName: string;
  lastName: string;
  displayName?: string;
  phoneNumber?: string;
  timezone?: string;
  locale?: string;
  department?: string;
  title?: string;
  manager?: string;
  location?: string;
  profileImage?: string;
  preferences?: UserPreferences;
  settings?: UserSettings;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  status: UserStatus;
  roles: string[];
  permissions: string[];
  clientAccountId?: string;
  engagements: string[];
  lastLoginAt?: string;
  lastActivityAt?: string;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
}

export interface UserProfile {
  userId: string;
  personalInfo: PersonalInfo;
  contactInfo: ContactInfo;
  professionalInfo: ProfessionalInfo;
  preferences: UserPreferences;
  settings: UserSettings;
  security: SecuritySettings;
}

// User Status Types
export type UserStatus = 'active' | 'inactive' | 'pending' | 'suspended' | 'deleted';

// Supporting interfaces referenced but defined in data-models module
export interface UserRole {
  roleId: string;
  name: string;
  scope?: string;
  assignedAt: string;
  expiresAt?: string;
}

export interface UserPermission {
  permissionId: string;
  name: string;
  resource: string;
  actions: string[];
  scope?: string;
}

export interface UserActivity {
  id: string;
  userId: string;
  action: string;
  resource: string;
  timestamp: string;
  metadata: Record<string, any>;
}

export interface UserEngagement {
  engagementId: string;
  name: string;
  role: string;
  status: string;
  startDate: string;
  endDate?: string;
}

export interface UserSummary {
  id: string;
  email: string;
  displayName: string;
  status: UserStatus;
  roles: string[];
  lastLoginAt?: string;
  createdAt: string;
}

export interface UserStatistics {
  total: number;
  active: number;
  inactive: number;
  pending: number;
  suspended: number;
  recentLogins: number;
}

export interface RoleDistribution {
  roleId: string;
  roleName: string;
  userCount: number;
  percentage: number;
}

export interface ActivitySummary {
  totalActions: number;
  uniqueUsers: number;
  topActions: Array<{
    action: string;
    count: number;
  }>;
  timeRange: {
    start: string;
    end: string;
  };
}

export interface UserChange {
  field: string;
  oldValue: any;
  newValue: any;
  changedAt: string;
  changedBy: string;
}

export interface UserNotification {
  type: string;
  recipient: string;
  channel: string;
  sent: boolean;
  sentAt?: string;
}

export interface UserDeactivation {
  userId: string;
  reason: string;
  deactivatedBy: string;
  dataRetention: {
    retainData: boolean;
    retentionPeriod?: string;
    deletionDate?: string;
  };
  ownership: {
    transferred: boolean;
    newOwnerId?: string;
    assetsTransferred: string[];
  };
}

// Additional supporting types that would be imported from data-models
export interface PersonalInfo {
  firstName: string;
  lastName: string;
  displayName?: string;
  dateOfBirth?: string;
  profileImage?: string;
}

export interface ContactInfo {
  email: string;
  phoneNumber?: string;
  address?: Address;
  emergencyContact?: EmergencyContact;
}

export interface ProfessionalInfo {
  title?: string;
  department?: string;
  manager?: string;
  location?: string;
  startDate?: string;
  employeeId?: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  dateFormat: string;
  notifications: NotificationPreferences;
}

export interface UserSettings {
  twoFactorEnabled: boolean;
  sessionTimeout: number;
  defaultDashboard?: string;
  accessibility: AccessibilitySettings;
}

export interface SecuritySettings {
  lastPasswordChange: string;
  loginAttempts: number;
  lockedUntil?: string;
  trustedDevices: TrustedDevice[];
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface EmergencyContact {
  name: string;
  relationship: string;
  phoneNumber: string;
  email?: string;
}

export interface NotificationPreferences {
  email: boolean;
  inApp: boolean;
  sms: boolean;
  categories: Record<string, boolean>;
}

export interface AccessibilitySettings {
  fontSize: 'small' | 'medium' | 'large';
  highContrast: boolean;
  screenReader: boolean;
  keyboardNavigation: boolean;
}

export interface TrustedDevice {
  deviceId: string;
  name: string;
  type: string;
  lastUsed: string;
  trusted: boolean;
}