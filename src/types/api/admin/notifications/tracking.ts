/**
 * Notification Tracking Types
 * 
 * Types for tracking notification engagement and analytics.
 * 
 * Generated with CC for modular admin type organization.
 */

import type { BaseMetadata, AuditableMetadata } from '../../../shared/metadata-types';
import type { ChannelType, TrackingEventType } from './enums';
import type { UtmParameters } from './notification';

// Notification tracking configuration
export interface NotificationTracking {
  trackOpens: boolean;
  trackClicks: boolean;
  trackConversions: boolean;
  utm_parameters?: UtmParameters;
  custom_properties?: Record<string, string | number | boolean | null>;
  events: TrackingEvent[];
}

// Tracking event record
export interface TrackingEvent {
  event_type: TrackingEventType;
  timestamp: string;
  recipient_id: string;
  channel: ChannelType;
  metadata: AuditableMetadata;
}