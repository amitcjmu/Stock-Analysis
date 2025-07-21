/**
 * RBAC utility functions for frontend role-based access control
 */

import { User } from '@/contexts/AuthContext/types';

// Role hierarchy mapping
export const RoleLevel = {
  PLATFORM_ADMIN: 'platform_admin',
  CLIENT_ADMIN: 'client_admin',
  ENGAGEMENT_MANAGER: 'engagement_manager',
  ANALYST: 'analyst',
  VIEWER: 'viewer',
  USER: 'user' // Legacy role mapped to viewer
} as const;

// Collection flow permissions by role
export const COLLECTION_PERMISSIONS = {
  canCreate: [
    RoleLevel.PLATFORM_ADMIN,
    RoleLevel.CLIENT_ADMIN,
    RoleLevel.ENGAGEMENT_MANAGER,
    RoleLevel.ANALYST,
    'admin', // Legacy
    'engagement_manager', // Legacy
    'analyst' // Legacy
  ],
  canEdit: [
    RoleLevel.PLATFORM_ADMIN,
    RoleLevel.CLIENT_ADMIN,
    RoleLevel.ENGAGEMENT_MANAGER,
    RoleLevel.ANALYST,
    'admin', // Legacy
    'engagement_manager', // Legacy
    'analyst' // Legacy
  ],
  canDelete: [
    RoleLevel.PLATFORM_ADMIN,
    RoleLevel.CLIENT_ADMIN,
    RoleLevel.ENGAGEMENT_MANAGER,
    'admin', // Legacy
    'engagement_manager' // Legacy
  ],
  canView: [
    RoleLevel.PLATFORM_ADMIN,
    RoleLevel.CLIENT_ADMIN,
    RoleLevel.ENGAGEMENT_MANAGER,
    RoleLevel.ANALYST,
    RoleLevel.VIEWER,
    RoleLevel.USER,
    'admin', // Legacy
    'engagement_manager', // Legacy
    'analyst', // Legacy
    'user', // Legacy
    'viewer' // Legacy
  ]
};

/**
 * Check if user has permission for a specific action
 */
export function hasPermission(user: User | null, permission: keyof typeof COLLECTION_PERMISSIONS): boolean {
  if (!user || !user.role) return false;
  
  const allowedRoles = COLLECTION_PERMISSIONS[permission];
  return allowedRoles.includes(user.role);
}

/**
 * Check if user can create collection flows
 */
export function canCreateCollectionFlow(user: User | null): boolean {
  return hasPermission(user, 'canCreate');
}

/**
 * Check if user can edit collection flows
 */
export function canEditCollectionFlow(user: User | null): boolean {
  return hasPermission(user, 'canEdit');
}

/**
 * Check if user can delete collection flows
 */
export function canDeleteCollectionFlow(user: User | null): boolean {
  return hasPermission(user, 'canDelete');
}

/**
 * Check if user can view collection flows
 */
export function canViewCollectionFlow(user: User | null): boolean {
  return hasPermission(user, 'canView');
}

/**
 * Get human-readable role name
 */
export function getRoleName(role: string | undefined): string {
  if (!role) return 'Unknown';
  
  const roleNames: Record<string, string> = {
    platform_admin: 'Platform Admin',
    client_admin: 'Client Admin',
    engagement_manager: 'Engagement Manager',
    analyst: 'Analyst',
    viewer: 'Viewer',
    user: 'User',
    admin: 'Admin'
  };
  
  return roleNames[role.toLowerCase()] || role;
}