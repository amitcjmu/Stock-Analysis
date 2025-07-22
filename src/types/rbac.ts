/**
 * Enhanced RBAC Type Definitions
 * Supports hierarchical role-based access control with soft delete management
 */

export enum RoleLevel {
  PLATFORM_ADMIN = 'platform_admin',
  CLIENT_ADMIN = 'client_admin', 
  ENGAGEMENT_MANAGER = 'engagement_manager',
  ANALYST = 'analyst',
  VIEWER = 'viewer',
  ANONYMOUS = 'anonymous'
}

export enum DataScope {
  PLATFORM = 'platform',
  CLIENT = 'client',
  ENGAGEMENT = 'engagement',
  DEMO_ONLY = 'demo_only'
}

export enum UserStatus {
  PENDING_APPROVAL = 'pending_approval',
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  DEACTIVATED = 'deactivated'
}

export enum DeletedItemType {
  CLIENT_ACCOUNT = 'client_account',
  ENGAGEMENT = 'engagement',
  DATA_IMPORT_SESSION = 'data_import_session',
  USER_PROFILE = 'user_profile'
}

export enum SoftDeleteStatus {
  PENDING_REVIEW = 'pending_review',
  APPROVED_FOR_PURGE = 'approved_for_purge',
  REJECTED = 'rejected',
  PURGED = 'purged',
  RESTORED = 'restored'
}

export interface EnhancedUserProfile {
  user_id: string;
  role_level: RoleLevel;
  data_scope: DataScope;
  scope_client_account_id?: string;
  scope_engagement_id?: string;
  status: UserStatus;
  approval_requested_at: string;
  approved_at?: string;
  approved_by?: string;
  registration_reason?: string;
  organization?: string;
  role_description?: string;
  phone_number?: string;
  manager_email?: string;
  linkedin_profile?: string;
  last_login_at?: string;
  login_count: number;
  failed_login_attempts: number;
  last_failed_login?: string;
  notification_preferences: {
    email_notifications: boolean;
    system_alerts: boolean;
    learning_updates: boolean;
    weekly_reports: boolean;
  };
  is_deleted: boolean;
  deleted_at?: string;
  deleted_by?: string;
  delete_reason?: string;
  created_at: string;
  updated_at?: string;
}

export interface RolePermissions {
  id: string;
  role_level: RoleLevel;
  can_manage_platform_settings: boolean;
  can_manage_all_clients: boolean;
  can_manage_all_users: boolean;
  can_purge_deleted_data: boolean;
  can_view_system_logs: boolean;
  can_create_clients: boolean;
  can_modify_client_settings: boolean;
  can_manage_client_users: boolean;
  can_delete_client_data: boolean;
  can_create_engagements: boolean;
  can_modify_engagement_settings: boolean;
  can_manage_engagement_users: boolean;
  can_delete_engagement_data: boolean;
  can_import_data: boolean;
  can_export_data: boolean;
  can_view_analytics: boolean;
  can_modify_data: boolean;
  can_configure_agents: boolean;
  can_view_agent_insights: boolean;
  can_approve_agent_decisions: boolean;
  created_at: string;
  updated_at?: string;
}

export interface SoftDeletedItem {
  id: string;
  item_type: DeletedItemType;
  item_id: string;
  item_name?: string;
  item_data?: Record<string, unknown>;
  client_account_id?: string;
  engagement_id?: string;
  client_account_name?: string;
  engagement_name?: string;
  deleted_by: string;
  deleted_by_name: string;
  deleted_by_email: string;
  deleted_at: string;
  delete_reason?: string;
  status: SoftDeleteStatus;
  reviewed_by?: string;
  reviewed_at?: string;
  review_decision?: 'approve' | 'reject';
  review_notes?: string;
  purged_at?: string;
  restored_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface AccessAuditLog {
  id: string;
  user_id: string;
  action_type: string;
  resource_type?: string;
  resource_id?: string;
  client_account_id?: string;
  engagement_id?: string;
  result: 'success' | 'denied' | 'error';
  reason?: string;
  ip_address?: string;
  user_agent?: string;
  details?: Record<string, string | number | boolean>;

  user_role_level?: RoleLevel;
  user_data_scope?: DataScope;
  created_at: string;
}

export interface UserAccessScope {
  client_account_ids: string[];
  engagement_ids: string[];
  scope: 'platform' | 'client' | 'engagement' | 'demo_only' | 'none';
  include_demo: boolean;
}

export interface PlatformAdminStats {
  pending_items: number;
  high_priority_items: number;
  recent_activity: number;
  total_managed_items: number;
}

export interface PurgeRequest {
  action: 'approve' | 'reject';
  item_id: string;
  notes: string;
}

export interface PurgeResponse {
  status: 'success' | 'error';
  message: string;
  item?: SoftDeletedItem;
}

// API Response Types
export interface PendingPurgeItemsResponse {
  status: string;
  pending_items: SoftDeletedItem[];
  stats: PlatformAdminStats;
}

export interface PlatformAdminStatsResponse {
  status: string;
  stats: PlatformAdminStats;
}

export interface AuditLogResponse {
  status: string;
  audit_logs: AccessAuditLog[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
} 