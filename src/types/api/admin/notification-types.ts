/**
 * Notification Management API Types
 * 
 * @deprecated This file has been modularized. Please import from specific modules:
 * - @/types/api/admin/notifications for all notification types
 * - @/types/api/admin/notifications/api-types for API request/response types
 * - @/types/api/admin/notifications/notification for core notification types
 * - @/types/api/admin/notifications/templates for template types
 * - @/types/api/admin/notifications/delivery for delivery types
 * - @/types/api/admin/notifications/tracking for tracking types
 * - @/types/api/admin/common for shared types like GeoLocation, DeviceInfo
 * 
 * This file now re-exports all types for backward compatibility.
 * 
 * Generated with CC for modular admin type organization.
 */

// Re-export all notification types for backward compatibility
export type * from './notifications';

// Re-export common types that were previously defined here
export type { 
  GeoLocation, 
  DeviceInfo 
} from './common';