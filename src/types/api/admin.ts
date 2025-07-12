/**
 * Admin API Types
 * 
 * Type definitions for Administrative APIs including user management, 
 * engagement management, system settings, and platform administration.
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
  DeleteResponse,
  ValidationResult
} from './shared';

// User Management APIs
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

// Role and Permission Management APIs
export interface CreateRoleRequest extends CreateRequest<RoleData> {
  data: RoleData;
  inheritFrom?: string;
  permissions: string[];
  clientAccountScoped?: boolean;
  engagementScoped?: boolean;
}

export interface CreateRoleResponse extends CreateResponse<Role> {
  data: Role;
  roleId: string;
  inheritedPermissions: string[];
  effectivePermissions: string[];
}

export interface GetRoleRequest extends GetRequest {
  roleId: string;
  includePermissions?: boolean;
  includeUsers?: boolean;
  includeInheritance?: boolean;
}

export interface GetRoleResponse extends GetResponse<Role> {
  data: Role;
  permissions: Permission[];
  users: RoleUser[];
  inheritance: RoleInheritance;
}

export interface AssignRoleRequest extends BaseApiRequest {
  userId: string;
  roleId: string;
  scope?: RoleScope;
  expiresAt?: string;
  conditions?: RoleCondition[];
  context: MultiTenantContext;
}

export interface AssignRoleResponse extends BaseApiResponse<RoleAssignment> {
  data: RoleAssignment;
  assignmentId: string;
  effectivePermissions: string[];
  scopeLimitations: string[];
}

export interface RevokeRoleRequest extends BaseApiRequest {
  userId: string;
  roleId: string;
  reason: string;
  immediateEffect?: boolean;
  notifyUser?: boolean;
  context: MultiTenantContext;
}

export interface RevokeRoleResponse extends BaseApiResponse<RoleRevocation> {
  data: RoleRevocation;
  revokedAt: string;
  remainingPermissions: string[];
  notificationSent: boolean;
}

// Client Account Management APIs
export interface CreateClientAccountRequest extends CreateRequest<ClientAccountData> {
  data: ClientAccountData;
  adminUser: AdminUserData;
  subscriptionPlan?: string;
  billingInfo?: BillingInformation;
  setupConfiguration?: AccountSetupConfig;
}

export interface CreateClientAccountResponse extends CreateResponse<ClientAccount> {
  data: ClientAccount;
  accountId: string;
  adminUser: User;
  subscriptionActive: boolean;
  setupCompleted: boolean;
}

export interface GetClientAccountRequest extends GetRequest {
  accountId: string;
  includeUsers?: boolean;
  includeEngagements?: boolean;
  includeSubscription?: boolean;
  includeBilling?: boolean;
  includeUsage?: boolean;
}

export interface GetClientAccountResponse extends GetResponse<ClientAccount> {
  data: ClientAccount;
  users: AccountUser[];
  engagements: AccountEngagement[];
  subscription: SubscriptionDetails;
  billing: BillingDetails;
  usage: UsageMetrics;
}

export interface ListClientAccountsRequest extends ListRequest {
  status?: AccountStatus[];
  subscriptionPlans?: string[];
  createdAfter?: string;
  createdBefore?: string;
  includeTrials?: boolean;
  includeInactive?: boolean;
}

export interface ListClientAccountsResponse extends ListResponse<ClientAccountSummary> {
  data: ClientAccountSummary[];
  statistics: AccountStatistics;
  subscriptionSummary: SubscriptionSummary;
  revenueSummary: RevenueSummary;
}

export interface UpdateClientAccountRequest extends UpdateRequest<Partial<ClientAccountData>> {
  accountId: string;
  data: Partial<ClientAccountData>;
  updateType?: 'profile' | 'subscription' | 'billing' | 'settings' | 'status';
  notifyAdmin?: boolean;
}

export interface UpdateClientAccountResponse extends UpdateResponse<ClientAccount> {
  data: ClientAccount;
  changes: AccountChange[];
  subscriptionChanges: SubscriptionChange[];
  billingChanges: BillingChange[];
}

// Engagement Management APIs
export interface CreateEngagementRequest extends CreateRequest<EngagementData> {
  clientAccountId: string;
  data: EngagementData;
  teamMembers: TeamMember[];
  objectives: EngagementObjective[];
  timeline: EngagementTimeline;
  budget?: EngagementBudget;
}

export interface CreateEngagementResponse extends CreateResponse<Engagement> {
  data: Engagement;
  engagementId: string;
  teamAssignments: TeamAssignment[];
  projectSetup: ProjectSetup;
  resourceAllocations: ResourceAllocation[];
}

export interface GetEngagementRequest extends GetRequest {
  engagementId: string;
  includeTeam?: boolean;
  includeFlows?: boolean;
  includeProgress?: boolean;
  includeBudget?: boolean;
  includeMetrics?: boolean;
}

export interface GetEngagementResponse extends GetResponse<Engagement> {
  data: Engagement;
  team: EngagementTeam;
  flows: EngagementFlow[];
  progress: EngagementProgress;
  budget: EngagementBudget;
  metrics: EngagementMetrics;
}

export interface ListEngagementsRequest extends ListRequest {
  clientAccountId?: string;
  status?: EngagementStatus[];
  types?: string[];
  startDateAfter?: string;
  startDateBefore?: string;
  endDateAfter?: string;
  endDateBefore?: string;
  includeCompleted?: boolean;
  includeArchived?: boolean;
}

export interface ListEngagementsResponse extends ListResponse<EngagementSummary> {
  data: EngagementSummary[];
  statistics: EngagementStatistics;
  statusDistribution: StatusDistribution[];
  timelineAnalysis: TimelineAnalysis;
}

export interface UpdateEngagementRequest extends UpdateRequest<Partial<EngagementData>> {
  engagementId: string;
  data: Partial<EngagementData>;
  updateType?: 'details' | 'team' | 'timeline' | 'budget' | 'status' | 'objectives';
  notifyTeam?: boolean;
}

export interface UpdateEngagementResponse extends UpdateResponse<Engagement> {
  data: Engagement;
  changes: EngagementChange[];
  teamNotifications: TeamNotification[];
  impactAnalysis: ChangeImpactAnalysis;
}

// System Settings APIs
export interface GetSystemSettingsRequest extends GetRequest {
  category?: 'security' | 'integration' | 'notification' | 'performance' | 'compliance';
  includeDefaults?: boolean;
  includeDescription?: boolean;
  includeValidation?: boolean;
}

export interface GetSystemSettingsResponse extends GetResponse<SystemSettings> {
  data: SystemSettings;
  categories: SettingCategory[];
  validation: SettingValidation[];
  dependencies: SettingDependency[];
}

export interface UpdateSystemSettingsRequest extends UpdateRequest<Partial<SystemSettingsData>> {
  data: Partial<SystemSettingsData>;
  category?: string;
  validateChanges?: boolean;
  notifyAdmins?: boolean;
  scheduleRestart?: boolean;
}

export interface UpdateSystemSettingsResponse extends UpdateResponse<SystemSettings> {
  data: SystemSettings;
  validationResults: SettingValidationResult[];
  changesApplied: SettingChange[];
  restartRequired: boolean;
}

export interface GetSystemHealthRequest extends BaseApiRequest {
  includeDetails?: boolean;
  includeMetrics?: boolean;
  includeAlerts?: boolean;
  includeDependencies?: boolean;
  context: MultiTenantContext;
}

export interface GetSystemHealthResponse extends BaseApiResponse<SystemHealth> {
  data: SystemHealth;
  components: ComponentHealth[];
  metrics: HealthMetrics;
  alerts: HealthAlert[];
  dependencies: DependencyHealth[];
}

// Audit and Logging APIs
export interface GetAuditLogsRequest extends ListRequest {
  userId?: string;
  action?: string;
  resource?: string;
  clientAccountId?: string;
  engagementId?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  severity?: AuditSeverity[];
  includeDetails?: boolean;
}

export interface GetAuditLogsResponse extends ListResponse<AuditLog> {
  data: AuditLog[];
  actionSummary: ActionSummary[];
  userActivity: UserActivitySummary[];
  securityEvents: SecurityEvent[];
}

export interface CreateAuditLogRequest extends CreateRequest<AuditLogData> {
  data: AuditLogData;
  severity: AuditSeverity;
  automated?: boolean;
  alertRequired?: boolean;
}

export interface CreateAuditLogResponse extends CreateResponse<AuditLog> {
  data: AuditLog;
  logId: string;
  alertTriggered: boolean;
  notificationsSent: string[];
}

export interface GetSecurityEventsRequest extends ListRequest {
  eventTypes?: SecurityEventType[];
  severity?: SecuritySeverity[];
  resolved?: boolean;
  timeRange?: {
    start: string;
    end: string;
  };
  includeContext?: boolean;
}

export interface GetSecurityEventsResponse extends ListResponse<SecurityEvent> {
  data: SecurityEvent[];
  threatLevel: ThreatLevel;
  incidentSummary: IncidentSummary;
  recommendations: SecurityRecommendation[];
}

// Analytics and Reporting APIs
export interface GetPlatformAnalyticsRequest extends BaseApiRequest {
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  includeForecasts?: boolean;
  context: MultiTenantContext;
}

export interface GetPlatformAnalyticsResponse extends BaseApiResponse<PlatformAnalytics> {
  data: PlatformAnalytics;
  usage: UsageAnalytics;
  performance: PerformanceAnalytics;
  adoption: AdoptionAnalytics;
  trends: AnalyticsTrend[];
  forecasts: AnalyticsForecast[];
}

export interface GenerateAdminReportRequest extends BaseApiRequest {
  reportType: 'usage' | 'performance' | 'security' | 'billing' | 'engagement' | 'user_activity';
  format: 'pdf' | 'html' | 'docx' | 'xlsx' | 'json';
  timeRange?: {
    start: string;
    end: string;
  };
  filters?: ReportFilter[];
  sections?: string[];
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateAdminReportResponse extends BaseApiResponse<AdminReport> {
  data: AdminReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Notification Management APIs
export interface CreateNotificationRequest extends CreateRequest<NotificationData> {
  data: NotificationData;
  recipients: NotificationRecipient[];
  channels: NotificationChannel[];
  priority: NotificationPriority;
  scheduling?: NotificationScheduling;
}

export interface CreateNotificationResponse extends CreateResponse<Notification> {
  data: Notification;
  notificationId: string;
  estimatedDelivery: string;
  deliveryChannels: DeliveryChannel[];
}

export interface GetNotificationsRequest extends ListRequest {
  recipientId?: string;
  status?: NotificationStatus[];
  priority?: NotificationPriority[];
  channels?: string[];
  read?: boolean;
  timeRange?: {
    start: string;
    end: string;
  };
}

export interface GetNotificationsResponse extends ListResponse<Notification> {
  data: Notification[];
  unreadCount: number;
  priorityCounts: PriorityCount[];
  channelStats: ChannelStats[];
}

export interface MarkNotificationReadRequest extends BaseApiRequest {
  notificationId: string;
  readBy: string;
  readAt?: string;
  context: MultiTenantContext;
}

export interface MarkNotificationReadResponse extends BaseApiResponse<NotificationRead> {
  data: NotificationRead;
  readAt: string;
  remainingUnread: number;
}

// Supporting Data Types
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

export interface ClientAccountData {
  name: string;
  displayName?: string;
  description?: string;
  industry?: string;
  size?: 'startup' | 'small' | 'medium' | 'large' | 'enterprise';
  website?: string;
  headquarters?: Address;
  contactInfo: ContactInfo;
  billingInfo?: BillingInformation;
  preferences?: AccountPreferences;
  settings?: AccountSettings;
}

export interface ClientAccount {
  id: string;
  name: string;
  displayName: string;
  status: AccountStatus;
  tier: AccountTier;
  subscription: SubscriptionInfo;
  users: number;
  engagements: number;
  createdAt: string;
  updatedAt: string;
  lastActivityAt?: string;
  metadata: Record<string, any>;
}

export interface EngagementData {
  name: string;
  description?: string;
  type: EngagementType;
  scope: EngagementScope;
  objectives: EngagementObjective[];
  timeline: EngagementTimeline;
  budget?: EngagementBudget;
  stakeholders: Stakeholder[];
  requirements: EngagementRequirement[];
  deliverables: Deliverable[];
  riskFactors: RiskFactor[];
  successCriteria: SuccessCriteria[];
}

export interface Engagement {
  id: string;
  clientAccountId: string;
  name: string;
  description: string;
  type: EngagementType;
  status: EngagementStatus;
  progress: number;
  startDate: string;
  endDate?: string;
  budget: EngagementBudget;
  team: EngagementTeam;
  flows: number;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  metadata: Record<string, any>;
}

export type UserStatus = 'active' | 'inactive' | 'pending' | 'suspended' | 'deleted';
export type AccountStatus = 'active' | 'trial' | 'suspended' | 'cancelled' | 'pending';
export type AccountTier = 'free' | 'basic' | 'professional' | 'enterprise' | 'custom';
export type EngagementType = 'discovery' | 'assessment' | 'migration' | 'modernization' | 'optimization' | 'consulting';
export type EngagementStatus = 'planning' | 'active' | 'on_hold' | 'completed' | 'cancelled';
export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';
export type SecurityEventType = 'login' | 'logout' | 'permission_change' | 'data_access' | 'configuration_change' | 'security_violation';
export type SecuritySeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';
export type ThreatLevel = 'minimal' | 'low' | 'moderate' | 'high' | 'severe';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';
export type NotificationStatus = 'pending' | 'sent' | 'delivered' | 'read' | 'failed';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)