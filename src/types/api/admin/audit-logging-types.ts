/**
 * Audit and Logging API Types
 * 
 * @deprecated This file has been modularized. Please import from specific modules:
 * - @/types/api/admin/audit for all audit types
 * - @/types/api/admin/audit/api-types for API request/response types
 * - @/types/api/admin/audit/audit-log for audit log types
 * - @/types/api/admin/audit/security-events for security event types
 * - @/types/api/admin/audit/activity for user activity types
 * - @/types/api/admin/common for shared types like GeoLocation, DeviceInfo
 * 
 * This file now re-exports all types for backward compatibility.
 * 
 * Generated with CC for modular admin type organization.
 */

// Re-export all audit types for backward compatibility
export * from './audit';

// Re-export common types that were previously defined here
export { 
  GeoLocation, 
  DeviceInfo,
  AuditMetadata,
  SecurityEventMetadata,
  ActivityLocation,
  ActivityDevice,
  TimeRange,
  Environment,
  SessionType,
  AuthenticationMethod,
  ChangeType,
  DataSensitivity,
  BusinessImpact,
  TechnicalImpact,
  ImpactLevel,
  ConfidenceLevel,
  TrendDirection,
  ComplexityLevel,
  EffortLevel,
  ResourceType
} from './common';