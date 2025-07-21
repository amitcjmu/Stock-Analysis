/**
 * Device Information Types
 * 
 * Common device-related type definitions used across admin modules
 * for tracking user devices, security, and analytics.
 * 
 * Generated with CC for modular admin type organization.
 */

/**
 * Device information for tracking and security
 */
export interface DeviceInfo {
  type: DeviceType;
  os: string;
  browser?: string;
  version?: string;
  mobile?: boolean;
  fingerprint?: string;
  trusted?: boolean;
  first_seen?: string;
  last_seen?: string;
  name?: string;
  model?: string;
}

/**
 * Device types
 */
export type DeviceType = 
  | 'desktop' 
  | 'mobile' 
  | 'tablet' 
  | 'tv' 
  | 'watch' 
  | 'speaker' 
  | 'server' 
  | 'iot' 
  | 'other' 
  | 'unknown';

/**
 * Trusted device information
 */
export interface TrustedDevice {
  id: string;
  device: DeviceInfo;
  trusted_at: string;
  trusted_by: string;
  expires_at?: string;
  last_used: string;
  location?: string;
  revoked?: boolean;
  revoked_at?: string;
  revoked_by?: string;
  revocation_reason?: string;
}

/**
 * Device activity tracking
 */
export interface ActivityDevice {
  device: DeviceInfo;
  count: number;
  first_seen: string;
  last_seen: string;
  risk_score: number;
}

/**
 * Device trust settings
 */
export interface TrustedDeviceSettings {
  enabled: boolean;
  max_devices: number;
  expiration_days: number;
  require_2fa: boolean;
  auto_revoke_inactive: boolean;
  inactive_days: number;
}