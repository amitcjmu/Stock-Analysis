/**
 * Geographic Location Types
 *
 * Common geographic and location-related type definitions used across
 * admin modules for audit logging, notifications, and analytics.
 *
 * Generated with CC for modular admin type organization.
 */

/**
 * Geographic location information
 */
export interface GeoLocation {
  country: string;
  region: string;
  city: string;
  latitude?: number;
  longitude?: number;
  timezone: string;
  isp?: string;
  is_vpn?: boolean;
  is_tor?: boolean;
}

/**
 * Geographic coordinates
 */
export interface GeographicCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number;
  altitudeAccuracy?: number;
}

/**
 * Physical address information
 */
export interface Address {
  street1: string;
  street2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
  coordinates?: GeographicCoordinates;
}

/**
 * Location-based restrictions
 */
export interface LocationRestriction {
  type: LocationRestrictionType;
  countries?: string[];
  regions?: string[];
  cities?: string[];
  ipRanges?: string[];
  coordinates?: GeographicBoundary;
}

/**
 * Geographic boundary definition
 */
export interface GeographicBoundary {
  center: GeographicCoordinates;
  radiusKm: number;
}

/**
 * Location restriction types
 */
export type LocationRestrictionType = 'allow' | 'deny';

/**
 * Location-based activity summary
 */
export interface ActivityLocation {
  location: GeoLocation;
  count: number;
  first_seen: string;
  last_seen: string;
  risk_score: number;
}
