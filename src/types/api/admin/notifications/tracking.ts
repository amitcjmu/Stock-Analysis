/**
 * Notification Tracking Types
 * 
 * Types for tracking notification engagement and analytics.
 * 
 * Generated with CC for modular admin type organization.
 */

import { ChannelType, TrackingEventType } from './enums';
import { UtmParameters } from './notification';

// Notification tracking configuration
export interface NotificationTracking {
  trackOpens: boolean;
  trackClicks: boolean;
  trackConversions: boolean;
  utm_parameters?: UtmParameters;
  custom_properties?: Record<string, any>;
  events: TrackingEvent[];
}

// Tracking event record
export interface TrackingEvent {
  event_type: TrackingEventType;
  timestamp: string;
  recipient_id: string;
  channel: ChannelType;
  metadata: Record<string, any>;
}