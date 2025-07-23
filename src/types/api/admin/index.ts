/**
 * Admin API Types - Module Index
 * 
 * Centralized export point for all admin-related type definitions.
 * This file exports all types from the modularized admin type modules.
 * 
 * Generated with CC for modular admin type organization.
 */

// Re-export all types from individual modules
export type * from './user-management-types';
export * from './role-permission-types';
export type * from './client-account-types';
export type * from './engagement-types';
export type * from './system-settings-types';
export type * from './audit-logging-types';
export type * from './analytics-reporting-types';
export type * from './notification-types';
export type * from './data-models';

// Module organization metadata for reference
export const ADMIN_TYPE_MODULES = {
  USER_MANAGEMENT: 'user-management-types',
  ROLE_PERMISSION: 'role-permission-types',
  CLIENT_ACCOUNT: 'client-account-types',
  ENGAGEMENT: 'engagement-types',
  SYSTEM_SETTINGS: 'system-settings-types',
  AUDIT_LOGGING: 'audit-logging-types',
  ANALYTICS_REPORTING: 'analytics-reporting-types',
  NOTIFICATION: 'notification-types',
  DATA_MODELS: 'data-models'
} as const;

// Type module descriptions for documentation
export const MODULE_DESCRIPTIONS = {
  [ADMIN_TYPE_MODULES.USER_MANAGEMENT]: 'User management operations including CRUD, lifecycle, and authentication workflows',
  [ADMIN_TYPE_MODULES.ROLE_PERMISSION]: 'Role-based access control including roles, permissions, and access management',
  [ADMIN_TYPE_MODULES.CLIENT_ACCOUNT]: 'Client account management including subscriptions, billing, and account lifecycle',
  [ADMIN_TYPE_MODULES.ENGAGEMENT]: 'Engagement lifecycle management including teams, progress tracking, and analytics',
  [ADMIN_TYPE_MODULES.SYSTEM_SETTINGS]: 'System configuration including settings, health monitoring, and administration',
  [ADMIN_TYPE_MODULES.AUDIT_LOGGING]: 'Audit trail management including security events and compliance tracking',
  [ADMIN_TYPE_MODULES.ANALYTICS_REPORTING]: 'Platform analytics including business intelligence and reporting',
  [ADMIN_TYPE_MODULES.NOTIFICATION]: 'Notification system management including delivery and templates',
  [ADMIN_TYPE_MODULES.DATA_MODELS]: 'Shared data types and entities used across admin modules'
} as const;

// Version information for the modularized types
export const ADMIN_TYPES_VERSION = '1.0.0';
export const LAST_UPDATED = '2025-07-19';
export const GENERATED_BY = 'Claude Code (CC)';

// Export type for module names
export type AdminTypeModule = typeof ADMIN_TYPE_MODULES[keyof typeof ADMIN_TYPE_MODULES];