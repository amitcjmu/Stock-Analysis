/**
 * Core Notification Types
 * 
 * Core notification data structures and interfaces.
 * 
 * Generated with CC for modular admin type organization.
 */

import type { BaseMetadata } from '../../../shared/metadata-types';
import { NotificationMetadata } from '../common';
import { 
  NotificationPriority, 
  NotificationStatus, 
  NotificationType, 
  NotificationCategory,
  NotificationSource,
  ChannelType
} from './enums';
import { NotificationDelivery } from './delivery';
import { NotificationTracking } from './tracking';
import { RecurringSchedule, ScheduleDelay, DeviceInfo, GeoLocation } from '../common';

// Core notification data structure
export interface NotificationData {
  title: string;
  content: NotificationContent;
  type: NotificationType;
  category: NotificationCategory;
  source: NotificationSource;
  metadata?: NotificationMetadata;
  actions?: NotificationAction[];
  tracking?: NotificationTracking;
  compliance?: NotificationCompliance;
}

// Full notification entity
export interface Notification {
  id: string;
  title: string;
  content: NotificationContent;
  type: NotificationType;
  category: NotificationCategory;
  priority: NotificationPriority;
  status: NotificationStatus;
  source: NotificationSource;
  recipients: NotificationRecipient[];
  channels: NotificationChannel[];
  delivery: NotificationDelivery;
  tracking: NotificationTracking;
  scheduling: NotificationScheduling;
  metadata: NotificationMetadata;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

// Notification content
export interface NotificationContent {
  subject?: string;
  body: string;
  summary?: string;
  html?: string;
  markdown?: string;
  variables?: BaseMetadata;
  template?: NotificationTemplate;
  attachments?: NotificationAttachment[];
  media?: NotificationMedia[];
}

// Notification recipient
export interface NotificationRecipient {
  id: string;
  type: RecipientType;
  address: string;
  name?: string;
  preferences?: RecipientPreferences;
  groups?: string[];
  roles?: string[];
  conditions?: RecipientCondition[];
  substitutions?: BaseMetadata;
}

// Notification channel configuration
export interface NotificationChannel {
  type: ChannelType;
  enabled: boolean;
  configuration: ChannelConfiguration;
  priority: number;
  fallback?: boolean;
  conditions?: ChannelCondition[];
  limits?: ChannelLimits;
}

// Notification scheduling
export interface NotificationScheduling {
  immediate: boolean;
  scheduledAt?: string;
  timezone?: string;
  recurring?: RecurringSchedule;
  delay?: ScheduleDelay;
  conditions?: SchedulingCondition[];
  optimization?: SchedulingOptimization;
}

// Notification read tracking
export interface NotificationRead {
  notificationId: string;
  recipientId: string;
  readAt: string;
  readBy: string;
  channel: ChannelType;
  device?: DeviceInfo;
  location?: GeoLocation;
  metadata: BaseMetadata;
}

// Delivery channel information
export interface DeliveryChannel {
  type: ChannelType;
  status: ChannelStatus;
  estimatedDelivery: string;
  configuration: ChannelConfiguration;
  limits: ChannelLimits;
}

// Priority statistics
export interface PriorityCount {
  priority: NotificationPriority;
  count: number;
  unread: number;
  percentage: number;
}

// Channel statistics
export interface ChannelStats {
  channel: ChannelType;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  failed: number;
  deliveryRate: number;
  openRate: number;
  clickRate: number;
}

// Supporting interfaces
export interface NotificationAction {
  id: string;
  label: string;
  url?: string;
  action?: string;
  style?: ActionStyle;
  confirmation?: boolean;
  tracking?: ActionTracking;
}

export interface NotificationCompliance {
  gdpr_consent: boolean;
  ccpa_consent: boolean;
  opt_out_available: boolean;
  retention_period?: string;
  data_processing_basis?: string;
  privacy_policy_url?: string;
}

export interface NotificationAttachment {
  filename: string;
  content_type: string;
  size: number;
  url?: string;
  content?: string;
  inline: boolean;
}

export interface NotificationMedia {
  type: MediaType;
  url: string;
  alt_text?: string;
  dimensions?: MediaDimensions;
  size?: number;
}

export interface MediaDimensions {
  width: number;
  height: number;
}

export interface ActionTracking {
  track_clicks: boolean;
  utm_parameters?: UtmParameters;
  custom_properties?: BaseMetadata;
}

export interface UtmParameters {
  source?: string;
  medium?: string;
  campaign?: string;
  term?: string;
  content?: string;
  custom?: Record<string, string>;
}

// Template reference (full template types in templates.ts)
export interface NotificationTemplate {
  id: string;
  name: string;
  version: string;
}

// Enums and types
export type RecipientType = 'user' | 'group' | 'role' | 'email' | 'phone' | 'device' | 'webhook';
export type ChannelStatus = 'active' | 'inactive' | 'suspended' | 'error' | 'rate_limited';
export type ActionStyle = 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'link';
export type MediaType = 'image' | 'video' | 'audio' | 'document' | 'gif' | 'svg';

// Import common types that are referenced
export type SchedulingCondition = import('../common').Condition;
export type ChannelCondition = import('../common').FieldCondition;
export type RecipientCondition = import('../common').Condition;

export interface RecipientPreferences {
  channels: ChannelPreference[];
  frequency: FrequencyPreference;
  categories: CategoryPreference[];
  quiet_hours?: import('../common').QuietHours;
  timezone?: string;
  language?: string;
}

export interface ChannelPreference {
  channel: ChannelType;
  enabled: boolean;
  priority: number;
}

export interface FrequencyPreference {
  immediate: boolean;
  digest: DigestFrequency;
  max_per_day?: number;
  max_per_week?: number;
}

export interface CategoryPreference {
  category: NotificationCategory;
  enabled: boolean;
  channels: ChannelType[];
}

export interface ChannelConfiguration {
  provider?: string;
  credentials?: BaseMetadata;
  settings: BaseMetadata;
  rate_limits?: import('../common').RateLimit[];
  retry_policy?: import('../common').RetryPolicy;
  fallback_channel?: ChannelType;
}

export interface ChannelLimits {
  rate_limit: import('../common').RateLimit;
  daily_limit?: number;
  monthly_limit?: number;
  concurrent_limit?: number;
  size_limit?: number;
}

export interface SchedulingOptimization {
  optimize_for: OptimizationGoal;
  respect_quiet_hours: boolean;
  timezone_optimization: boolean;
  frequency_capping: boolean;
  send_time_optimization: boolean;
}

export type DigestFrequency = 'hourly' | 'daily' | 'weekly' | 'monthly';
export type OptimizationGoal = 'delivery_rate' | 'open_rate' | 'click_rate' | 'conversion_rate' | 'engagement';