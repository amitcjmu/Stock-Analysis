/**
 * Permissions and Authorization Types
 * 
 * Permission checking, role management, and authorization API types.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../shared';

import type { UserPermissions, Role, ResourceAccess } from './core-types';
import { Permission } from './core-types';

// Permission and Authorization APIs
export interface GetUserPermissionsRequest extends BaseApiRequest {
  userId?: string;
  resourceType?: string;
  resourceId?: string;
  context: MultiTenantContext;
}

export interface GetUserPermissionsResponse extends BaseApiResponse<UserPermissions> {
  data: UserPermissions;
  effectivePermissions: string[];
  inheritedPermissions: string[];
  directPermissions: string[];
}

export interface CheckPermissionRequest extends BaseApiRequest {
  userId?: string;
  permission: string;
  resourceType?: string;
  resourceId?: string;
  context: MultiTenantContext;
}

export interface CheckPermissionResponse extends BaseApiResponse<unknown> {
  data: unknown;
  hasPermission: boolean;
  reason?: string;
  inheritedFrom?: string;
  conditions?: Record<string, unknown>;
}

export interface GetUserRolesRequest extends BaseApiRequest {
  userId?: string;
  includeInherited?: boolean;
  context: MultiTenantContext;
}

export interface GetUserRolesResponse extends BaseApiResponse<Role[]> {
  data: Role[];
  directRoles: Role[];
  inheritedRoles: Role[];
  effectivePermissions: string[];
}

export interface AssignRoleRequest extends BaseApiRequest {
  userId: string;
  roleId: string;
  resourceType?: string;
  resourceId?: string;
  expiresAt?: string;
  context: MultiTenantContext;
}

export interface AssignRoleResponse extends BaseApiResponse<unknown> {
  data: unknown;
  assigned: boolean;
  roleApplied: boolean;
  permissionsUpdated: string[];
}

export interface RevokeRoleRequest extends BaseApiRequest {
  userId: string;
  roleId: string;
  resourceType?: string;
  resourceId?: string;
  context: MultiTenantContext;
}

export interface RevokeRoleResponse extends BaseApiResponse<unknown> {
  data: unknown;
  revoked: boolean;
  permissionsRemoved: string[];
  effectivePermissions: string[];
}

export interface GetResourceAccessRequest extends BaseApiRequest {
  resourceType: string;
  resourceId: string;
  userId?: string;
  context: MultiTenantContext;
}

export interface GetResourceAccessResponse extends BaseApiResponse<ResourceAccess> {
  data: ResourceAccess;
  canRead: boolean;
  canWrite: boolean;
  canDelete: boolean;
  canShare: boolean;
  accessLevel: string;
}