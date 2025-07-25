/**
 * Notification Delivery Types
 *
 * Types related to notification delivery, tracking, and status management.
 *
 * Generated with CC for modular admin type organization.
 */

import type { BaseMetadata, AuditableMetadata } from '../../../shared/metadata-types';
import type { ChannelType, DeliveryStatus, ErrorCategory } from './enums';

// Notification delivery information
export interface NotificationDelivery {
  status: DeliveryStatus;
  attempts: DeliveryAttempt[];
  results: DeliveryResult[];
  metrics: DeliveryMetrics;
  errors: DeliveryError[];
  tracking: DeliveryTracking;
}

// Delivery attempt record
export interface DeliveryAttempt {
  attempt_number: number;
  channel: ChannelType;
  status: DeliveryStatus;
  attempted_at: string;
  completed_at?: string;
  error?: DeliveryError;
  metadata: AuditableMetadata;
}

// Delivery result per recipient/channel
export interface DeliveryResult {
  channel: ChannelType;
  recipient_id: string;
  status: DeliveryStatus;
  delivered_at?: string;
  message_id?: string;
  provider_response?: BaseMetadata;
  tracking_id?: string;
}

// Delivery metrics summary
export interface DeliveryMetrics {
  total_recipients: number;
  sent: number;
  delivered: number;
  bounced: number;
  failed: number;
  opened?: number;
  clicked?: number;
  converted?: number;
  unsubscribed?: number;
  spam_reported?: number;
}

// Delivery error information
export interface DeliveryError {
  code: string;
  message: string;
  category: ErrorCategory;
  retry_after?: number;
  permanent: boolean;
  provider_error?: BaseMetadata;
}

// Delivery tracking configuration
export interface DeliveryTracking {
  tracking_id: string;
  pixel_url?: string;
  click_tracking_enabled: boolean;
  open_tracking_enabled: boolean;
  unsubscribe_url?: string;
  preference_center_url?: string;
}
