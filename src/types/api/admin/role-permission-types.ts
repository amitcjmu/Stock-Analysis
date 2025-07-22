/**
 * Role and Permission Management API Types
 * 
 * Type definitions for role-based access control (RBAC) including role creation,
 * permission assignment, role inheritance, and access control management.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  GetRequest,
  GetResponse,
  CreateRequest,
  CreateResponse
} from '../shared';

// Role Creation APIs
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

// Role Retrieval APIs
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

// Role Assignment APIs
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

// Role Revocation APIs
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

// Supporting Types for Role Management
export interface RoleData {
  name: string;
  displayName?: string;
  description?: string;
  category?: RoleCategory;
  level?: RoleLevel;
  scope?: RoleScope;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface Role {
  id: string;
  name: string;
  displayName: string;
  description: string;
  category: RoleCategory;
  level: RoleLevel;
  scope: RoleScope;
  permissions: string[];
  inheritedFrom?: string[];
  isSystem: boolean;
  isCustom: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  metadata: Record<string, string | number | boolean | null>;
}

export interface Permission {
  id: string;
  name: string;
  displayName: string;
  description: string;
  resource: string;
  actions: PermissionAction[];
  scope: PermissionScope;
  category: PermissionCategory;
  isSystem: boolean;
  dependencies?: string[];
  conflicts?: string[];
  metadata: Record<string, string | number | boolean | null>;
}

export interface RoleUser {
  userId: string;
  email: string;
  displayName: string;
  assignedAt: string;
  assignedBy: string;
  expiresAt?: string;
  scope?: RoleScope;
  conditions?: RoleCondition[];
  status: RoleAssignmentStatus;
}

export interface RoleInheritance {
  roleId: string;
  inheritsFrom: RoleInheritanceRelation[];
  inheritedBy: RoleInheritanceRelation[];
  effectivePermissions: string[];
  permissionSources: PermissionSource[];
}

export interface RoleInheritanceRelation {
  roleId: string;
  roleName: string;
  level: number;
  permissions: string[];
}

export interface PermissionSource {
  permissionId: string;
  source: 'direct' | 'inherited';
  sourceRoleId?: string;
  sourceRoleName?: string;
}

export interface RoleAssignment {
  id: string;
  userId: string;
  roleId: string;
  roleName: string;
  assignedAt: string;
  assignedBy: string;
  expiresAt?: string;
  scope?: RoleScope;
  conditions?: RoleCondition[];
  status: RoleAssignmentStatus;
  effectivePermissions: string[];
  metadata: Record<string, string | number | boolean | null>;
}

export interface RoleRevocation {
  assignmentId: string;
  userId: string;
  roleId: string;
  roleName: string;
  revokedAt: string;
  revokedBy: string;
  reason: string;
  immediateEffect: boolean;
  remainingRoles: string[];
  remainingPermissions: string[];
}

export interface RoleScope {
  type: RoleScopeType;
  clientAccountId?: string;
  engagementId?: string;
  resourceIds?: string[];
  limitations?: ScopeLimitation[];
}

export interface RoleCondition {
  type: RoleConditionType;
  operator: ConditionOperator;
  value: unknown;
  description?: string;
}

export interface ScopeLimitation {
  resource: string;
  actions: string[];
  restrictions: Record<string, string | number | boolean | null>;
}

// Role and Permission Enums and Types
export type RoleCategory = 
  | 'system' 
  | 'administrative' 
  | 'operational' 
  | 'analytical' 
  | 'readonly' 
  | 'custom';

export type RoleLevel = 
  | 'global' 
  | 'organization' 
  | 'account' 
  | 'engagement' 
  | 'resource';

export type RoleScopeType = 
  | 'global' 
  | 'client_account' 
  | 'engagement' 
  | 'resource_specific';

export type RoleAssignmentStatus = 
  | 'active' 
  | 'inactive' 
  | 'suspended' 
  | 'expired' 
  | 'pending';

export type RoleConditionType = 
  | 'time_based' 
  | 'location_based' 
  | 'ip_restriction' 
  | 'mfa_required' 
  | 'approval_required';

export type ConditionOperator = 
  | 'equals' 
  | 'not_equals' 
  | 'contains' 
  | 'not_contains' 
  | 'greater_than' 
  | 'less_than' 
  | 'in' 
  | 'not_in';

export type PermissionAction = 
  | 'create' 
  | 'read' 
  | 'update' 
  | 'delete' 
  | 'execute' 
  | 'manage' 
  | 'view' 
  | 'edit' 
  | 'approve' 
  | 'reject';

export type PermissionScope = 
  | 'global' 
  | 'tenant' 
  | 'account' 
  | 'engagement' 
  | 'resource' 
  | 'own';

export type PermissionCategory = 
  | 'user_management' 
  | 'account_management' 
  | 'engagement_management' 
  | 'system_administration' 
  | 'data_access' 
  | 'analytics' 
  | 'security' 
  | 'billing' 
  | 'support';

// Permission Resource Constants
export const PERMISSION_RESOURCES = {
  USERS: 'users',
  ROLES: 'roles',
  PERMISSIONS: 'permissions',
  CLIENT_ACCOUNTS: 'client_accounts',
  ENGAGEMENTS: 'engagements',
  FLOWS: 'flows',
  DATA: 'data',
  ANALYTICS: 'analytics',
  REPORTS: 'reports',
  SYSTEM_SETTINGS: 'system_settings',
  AUDIT_LOGS: 'audit_logs',
  NOTIFICATIONS: 'notifications',
  BILLING: 'billing',
  SUPPORT: 'support'
} as const;

// Standard Role Names
export const STANDARD_ROLES = {
  SUPER_ADMIN: 'super_admin',
  PLATFORM_ADMIN: 'platform_admin',
  CLIENT_ADMIN: 'client_admin',
  ENGAGEMENT_MANAGER: 'engagement_manager',
  ANALYST: 'analyst',
  VIEWER: 'viewer',
  AUDITOR: 'auditor',
  SUPPORT: 'support'
} as const;

// Permission Validation Helpers
export interface PermissionCheck {
  userId: string;
  resource: string;
  action: string;
  scope?: RoleScope;
  context?: Record<string, string | number | boolean | null>;
}

export interface PermissionResult {
  allowed: boolean;
  reason?: string;
  conditions?: RoleCondition[];
  limitations?: ScopeLimitation[];
  effectiveRole?: string;
  metadata?: Record<string, string | number | boolean | null>;
}