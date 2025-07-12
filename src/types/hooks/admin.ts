/**
 * Admin Hook Types
 * 
 * Type definitions for administrative hooks including user management,
 * system administration, monitoring, and platform management patterns.
 */

import { BaseAsyncHookParams, BaseAsyncHookReturn } from './shared';

// User Management Hook Types
export interface UseUserManagementParams extends BaseAsyncHookParams {
  includeInactive?: boolean;
  includeDeleted?: boolean;
  filterByRole?: string[];
  filterByStatus?: UserStatus[];
  searchQuery?: string;
  sortBy?: UserSortField;
  sortDirection?: 'asc' | 'desc';
  pageSize?: number;
  onUserChange?: (userId: string, change: UserChange) => void;
  onUserCreated?: (user: User) => void;
  onUserDeleted?: (userId: string) => void;
}

export interface UseUserManagementReturn extends BaseAsyncHookReturn<User[]> {
  users: User[];
  activeUsers: User[];
  inactiveUsers: User[];
  deletedUsers: User[];
  totalUsers: number;
  
  // User CRUD operations
  createUser: (userData: CreateUserData) => Promise<User>;
  updateUser: (userId: string, updates: Partial<UserData>) => Promise<User>;
  deleteUser: (userId: string, soft?: boolean) => Promise<void>;
  restoreUser: (userId: string) => Promise<User>;
  activateUser: (userId: string) => Promise<User>;
  deactivateUser: (userId: string, reason?: string) => Promise<User>;
  
  // Role management
  assignRole: (userId: string, roleId: string, scope?: RoleScope) => Promise<void>;
  revokeRole: (userId: string, roleId: string) => Promise<void>;
  getUserRoles: (userId: string) => Promise<UserRole[]>;
  updateUserRoles: (userId: string, roleIds: string[]) => Promise<void>;
  
  // Permission management
  grantPermission: (userId: string, permission: string, scope?: PermissionScope) => Promise<void>;
  revokePermission: (userId: string, permission: string) => Promise<void>;
  getUserPermissions: (userId: string) => Promise<UserPermission[]>;
  checkUserPermission: (userId: string, permission: string, resource?: string) => Promise<boolean>;
  
  // User profiles
  getUserProfile: (userId: string) => Promise<UserProfile>;
  updateUserProfile: (userId: string, profileData: Partial<UserProfileData>) => Promise<UserProfile>;
  uploadUserAvatar: (userId: string, file: File) => Promise<string>;
  
  // Bulk operations
  bulkUpdateUsers: (userIds: string[], updates: Partial<UserData>) => Promise<BulkUpdateResult>;
  bulkDeleteUsers: (userIds: string[], soft?: boolean) => Promise<BulkDeleteResult>;
  bulkAssignRole: (userIds: string[], roleId: string) => Promise<BulkAssignResult>;
  importUsers: (file: File, options?: ImportOptions) => Promise<ImportResult>;
  exportUsers: (userIds?: string[], format?: ExportFormat) => Promise<ExportResult>;
  
  // Search and filtering
  searchUsers: (query: string, options?: SearchOptions) => Promise<User[]>;
  filterUsers: (criteria: UserFilterCriteria) => User[];
  sortUsers: (field: UserSortField, direction: 'asc' | 'desc') => void;
  
  // Statistics
  userStatistics: UserStatistics;
  getUserAnalytics: (timeRange?: TimeRange) => Promise<UserAnalytics>;
  
  // Session management
  getUserSessions: (userId: string) => Promise<UserSession[]>;
  revokeUserSession: (userId: string, sessionId: string) => Promise<void>;
  revokeAllUserSessions: (userId: string) => Promise<void>;
}

// Role Management Hook Types
export interface UseRoleManagementParams extends BaseAsyncHookParams {
  includeSystemRoles?: boolean;
  includeCustomRoles?: boolean;
  includePermissions?: boolean;
  includeUserCounts?: boolean;
  onRoleChange?: (roleId: string, change: RoleChange) => void;
}

export interface UseRoleManagementReturn extends BaseAsyncHookReturn<Role[]> {
  roles: Role[];
  systemRoles: Role[];
  customRoles: Role[];
  totalRoles: number;
  
  // Role CRUD operations
  createRole: (roleData: CreateRoleData) => Promise<Role>;
  updateRole: (roleId: string, updates: Partial<RoleData>) => Promise<Role>;
  deleteRole: (roleId: string) => Promise<void>;
  cloneRole: (roleId: string, newName: string) => Promise<Role>;
  
  // Permission management
  addPermissionToRole: (roleId: string, permission: string) => Promise<void>;
  removePermissionFromRole: (roleId: string, permission: string) => Promise<void>;
  updateRolePermissions: (roleId: string, permissions: string[]) => Promise<void>;
  getRolePermissions: (roleId: string) => Promise<Permission[]>;
  
  // Role hierarchy
  setRoleParent: (roleId: string, parentRoleId: string) => Promise<void>;
  removeRoleParent: (roleId: string) => Promise<void>;
  getRoleHierarchy: (roleId: string) => Promise<RoleHierarchy>;
  
  // Role assignments
  getRoleUsers: (roleId: string) => Promise<RoleUser[]>;
  assignRoleToUsers: (roleId: string, userIds: string[]) => Promise<void>;
  removeRoleFromUsers: (roleId: string, userIds: string[]) => Promise<void>;
  
  // Role validation
  validateRole: (roleData: RoleData) => Promise<RoleValidationResult>;
  checkRoleConflicts: (roleId: string, permissions: string[]) => Promise<RoleConflict[]>;
  
  // Role statistics
  roleStatistics: RoleStatistics;
  getRoleAnalytics: () => Promise<RoleAnalytics>;
}

// System Settings Hook Types
export interface UseSystemSettingsParams extends BaseAsyncHookParams {
  category?: SettingCategory;
  includeDefaults?: boolean;
  includeValidation?: boolean;
  onSettingChange?: (key: string, newValue: any, oldValue: any) => void;
  onValidationError?: (key: string, error: ValidationError) => void;
}

export interface UseSystemSettingsReturn extends BaseAsyncHookReturn<SystemSettings> {
  settings: SystemSettings;
  categories: SettingCategory[];
  
  // Setting operations
  getSetting: (key: string) => any;
  setSetting: (key: string, value: any) => Promise<void>;
  resetSetting: (key: string) => Promise<void>;
  updateSettings: (settings: Record<string, any>) => Promise<void>;
  
  // Setting categories
  getCategorySettings: (category: SettingCategory) => Record<string, any>;
  updateCategorySettings: (category: SettingCategory, settings: Record<string, any>) => Promise<void>;
  resetCategorySettings: (category: SettingCategory) => Promise<void>;
  
  // Validation
  validateSetting: (key: string, value: any) => Promise<SettingValidationResult>;
  validateAllSettings: () => Promise<SystemSettingsValidationResult>;
  
  // Import/Export
  exportSettings: (categories?: SettingCategory[]) => Promise<SettingsExport>;
  importSettings: (settingsData: SettingsImport, merge?: boolean) => Promise<SettingsImportResult>;
  
  // Default values
  getDefaultValue: (key: string) => any;
  resetToDefaults: (keys?: string[]) => Promise<void>;
  
  // Setting history
  getSettingHistory: (key: string) => Promise<SettingHistoryEntry[]>;
  revertSetting: (key: string, timestamp: number) => Promise<void>;
  
  // System restart
  requiresRestart: boolean;
  changedSettings: string[];
  scheduleRestart: (delay?: number) => Promise<void>;
  cancelScheduledRestart: () => Promise<void>;
}

// System Health Hook Types
export interface UseSystemHealthParams extends BaseAsyncHookParams {
  includeDetails?: boolean;
  includeMetrics?: boolean;
  includeAlerts?: boolean;
  includeDependencies?: boolean;
  refreshInterval?: number;
  onHealthChange?: (health: SystemHealth) => void;
  onAlert?: (alert: HealthAlert) => void;
}

export interface UseSystemHealthReturn extends BaseAsyncHookReturn<SystemHealth> {
  health: SystemHealth;
  overallStatus: HealthStatus;
  components: ComponentHealth[];
  dependencies: DependencyHealth[];
  alerts: HealthAlert[];
  metrics: HealthMetrics;
  
  // Health monitoring
  checkHealth: () => Promise<SystemHealth>;
  checkComponentHealth: (componentId: string) => Promise<ComponentHealth>;
  checkDependencyHealth: (dependencyId: string) => Promise<DependencyHealth>;
  
  // Component management
  getComponent: (componentId: string) => ComponentHealth | null;
  restartComponent: (componentId: string) => Promise<void>;
  stopComponent: (componentId: string) => Promise<void>;
  startComponent: (componentId: string) => Promise<void>;
  
  // Dependency management
  getDependency: (dependencyId: string) => DependencyHealth | null;
  testDependency: (dependencyId: string) => Promise<DependencyTestResult>;
  
  // Alert management
  acknowledgeAlert: (alertId: string) => Promise<void>;
  resolveAlert: (alertId: string, resolution?: string) => Promise<void>;
  muteAlert: (alertId: string, duration?: number) => Promise<void>;
  
  // Metrics
  getMetric: (metricName: string) => MetricValue | null;
  getMetricHistory: (metricName: string, timeRange: TimeRange) => Promise<MetricDataPoint[]>;
  
  // Health checks
  scheduleHealthCheck: (componentId: string, interval: number) => Promise<void>;
  cancelHealthCheck: (componentId: string) => Promise<void>;
  
  // System maintenance
  enterMaintenanceMode: (reason: string, duration?: number) => Promise<void>;
  exitMaintenanceMode: () => Promise<void>;
  isMaintenanceMode: boolean;
  maintenanceInfo: MaintenanceInfo | null;
}

// Audit Log Hook Types
export interface UseAuditLogParams extends BaseAsyncHookParams {
  userId?: string;
  action?: string;
  resource?: string;
  timeRange?: TimeRange;
  severity?: AuditSeverity[];
  includeDetails?: boolean;
  pageSize?: number;
  realTimeUpdates?: boolean;
  onNewEntry?: (entry: AuditLogEntry) => void;
}

export interface UseAuditLogReturn extends BaseAsyncHookReturn<AuditLogEntry[]> {
  entries: AuditLogEntry[];
  totalEntries: number;
  
  // Log querying
  searchLogs: (query: string, options?: LogSearchOptions) => Promise<AuditLogEntry[]>;
  filterLogs: (criteria: AuditLogFilterCriteria) => AuditLogEntry[];
  getLogEntry: (entryId: string) => Promise<AuditLogEntry>;
  
  // Log analysis
  getActionSummary: (timeRange?: TimeRange) => Promise<ActionSummary[]>;
  getUserActivity: (userId: string, timeRange?: TimeRange) => Promise<UserActivitySummary>;
  getResourceActivity: (resource: string, timeRange?: TimeRange) => Promise<ResourceActivitySummary>;
  
  // Security events
  getSecurityEvents: (timeRange?: TimeRange) => Promise<SecurityEvent[]>;
  getFailedLogins: (timeRange?: TimeRange) => Promise<FailedLoginAttempt[]>;
  getSuspiciousActivity: (timeRange?: TimeRange) => Promise<SuspiciousActivity[]>;
  
  // Compliance
  generateComplianceReport: (standard: ComplianceStandard, timeRange: TimeRange) => Promise<ComplianceReport>;
  exportAuditTrail: (criteria: ExportCriteria, format: ExportFormat) => Promise<AuditExport>;
  
  // Log management
  archiveLogs: (olderThan: Date) => Promise<ArchiveResult>;
  purgeLogs: (olderThan: Date) => Promise<PurgeResult>;
  
  // Real-time monitoring
  subscribeToEvents: (criteria: EventSubscriptionCriteria, callback: AuditEventCallback) => () => void;
  getActiveUsers: () => Promise<ActiveUser[]>;
  getCurrentSessions: () => Promise<ActiveSession[]>;
}

// Analytics and Reporting Hook Types
export interface UseAdminAnalyticsParams extends BaseAsyncHookParams {
  timeRange?: TimeRange;
  metrics?: string[];
  dimensions?: string[];
  includeComparisons?: boolean;
  includeTrends?: boolean;
  includeForecasts?: boolean;
  onAnalyticsUpdate?: (analytics: AdminAnalytics) => void;
}

export interface UseAdminAnalyticsReturn extends BaseAsyncHookReturn<AdminAnalytics> {
  analytics: AdminAnalytics;
  userAnalytics: UserAnalytics;
  systemAnalytics: SystemAnalytics;
  securityAnalytics: SecurityAnalytics;
  performanceAnalytics: PerformanceAnalytics;
  
  // Dashboard metrics
  getDashboardMetrics: () => Promise<DashboardMetrics>;
  getKPIs: () => Promise<KPIMetrics>;
  getAlerts: () => Promise<AlertSummary>;
  
  // User analytics
  getUserGrowth: (timeRange: TimeRange) => Promise<GrowthMetrics>;
  getUserEngagement: (timeRange: TimeRange) => Promise<EngagementMetrics>;
  getUserRetention: (timeRange: TimeRange) => Promise<RetentionMetrics>;
  
  // System analytics
  getSystemUsage: (timeRange: TimeRange) => Promise<UsageMetrics>;
  getPerformanceMetrics: (timeRange: TimeRange) => Promise<PerformanceMetrics>;
  getResourceUtilization: (timeRange: TimeRange) => Promise<ResourceUtilization>;
  
  // Security analytics
  getSecurityMetrics: (timeRange: TimeRange) => Promise<SecurityMetrics>;
  getThreatAnalysis: (timeRange: TimeRange) => Promise<ThreatAnalysis>;
  getVulnerabilityReport: () => Promise<VulnerabilityReport>;
  
  // Custom reports
  createReport: (reportConfig: ReportConfiguration) => Promise<AdminReport>;
  scheduleReport: (reportId: string, schedule: ReportSchedule) => Promise<void>;
  getScheduledReports: () => Promise<ScheduledReport[]>;
  
  // Export capabilities
  exportAnalytics: (format: ExportFormat, options?: ExportOptions) => Promise<AnalyticsExport>;
  exportReport: (reportId: string, format: ExportFormat) => Promise<ReportExport>;
}

// Notification Management Hook Types
export interface UseNotificationManagementParams extends BaseAsyncHookParams {
  includeRead?: boolean;
  includeArchived?: boolean;
  filterByType?: NotificationType[];
  filterByPriority?: NotificationPriority[];
  recipientId?: string;
  timeRange?: TimeRange;
  onNotificationReceived?: (notification: Notification) => void;
}

export interface UseNotificationManagementReturn extends BaseAsyncHookReturn<Notification[]> {
  notifications: Notification[];
  unreadNotifications: Notification[];
  readNotifications: Notification[];
  archivedNotifications: Notification[];
  totalNotifications: number;
  unreadCount: number;
  
  // Notification CRUD
  createNotification: (notificationData: CreateNotificationData) => Promise<Notification>;
  updateNotification: (notificationId: string, updates: Partial<NotificationData>) => Promise<Notification>;
  deleteNotification: (notificationId: string) => Promise<void>;
  
  // Notification status
  markAsRead: (notificationId: string) => Promise<void>;
  markAsUnread: (notificationId: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  archiveNotification: (notificationId: string) => Promise<void>;
  
  // Bulk operations
  bulkMarkAsRead: (notificationIds: string[]) => Promise<void>;
  bulkArchive: (notificationIds: string[]) => Promise<void>;
  bulkDelete: (notificationIds: string[]) => Promise<void>;
  
  // Notification channels
  getChannels: () => Promise<NotificationChannel[]>;
  updateChannelSettings: (channelId: string, settings: ChannelSettings) => Promise<void>;
  testChannel: (channelId: string) => Promise<ChannelTestResult>;
  
  // Templates
  getTemplates: () => Promise<NotificationTemplate[]>;
  createTemplate: (templateData: NotificationTemplateData) => Promise<NotificationTemplate>;
  updateTemplate: (templateId: string, updates: Partial<NotificationTemplateData>) => Promise<NotificationTemplate>;
  
  // Subscription management
  getSubscriptions: (userId?: string) => Promise<NotificationSubscription[]>;
  updateSubscription: (subscriptionId: string, settings: SubscriptionSettings) => Promise<void>;
  
  // Analytics
  getNotificationAnalytics: (timeRange?: TimeRange) => Promise<NotificationAnalytics>;
  getDeliveryMetrics: (timeRange?: TimeRange) => Promise<DeliveryMetrics>;
  getEngagementMetrics: (timeRange?: TimeRange) => Promise<EngagementMetrics>;
}

// Supporting Types
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  status: UserStatus;
  roles: string[];
  permissions: string[];
  lastLoginAt?: string;
  createdAt: string;
  updatedAt: string;
  metadata: Record<string, any>;
}

export interface Role {
  id: string;
  name: string;
  description?: string;
  permissions: string[];
  isSystem: boolean;
  parentRole?: string;
  userCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface SystemHealth {
  overallStatus: HealthStatus;
  components: ComponentHealth[];
  dependencies: DependencyHealth[];
  alerts: HealthAlert[];
  metrics: HealthMetrics;
  lastChecked: string;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  userId: string;
  action: string;
  resource: string;
  resourceId?: string;
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  severity: AuditSeverity;
  success: boolean;
}

export type UserStatus = 'active' | 'inactive' | 'pending' | 'suspended' | 'deleted';
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';
export type SettingCategory = 'general' | 'security' | 'integration' | 'notification' | 'performance' | 'compliance';
export type NotificationType = 'info' | 'warning' | 'error' | 'success' | 'system' | 'user';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';
export type UserSortField = 'name' | 'email' | 'status' | 'lastLogin' | 'createdAt';
export type ExportFormat = 'csv' | 'xlsx' | 'pdf' | 'json';
export type ComplianceStandard = 'sox' | 'gdpr' | 'hipaa' | 'pci' | 'iso27001';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)