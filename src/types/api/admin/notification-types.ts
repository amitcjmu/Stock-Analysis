/**
 * Notification Management API Types
 * 
 * Type definitions for notification system management including notification
 * creation, delivery, templates, and communication channel administration.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ListRequest,
  ListResponse,
  CreateRequest,
  CreateResponse
} from '../shared';

// Notification Creation APIs
export interface CreateNotificationRequest extends CreateRequest<NotificationData> {
  data: NotificationData;
  recipients: NotificationRecipient[];
  channels: NotificationChannel[];
  priority: NotificationPriority;
  scheduling?: NotificationScheduling;
}

export interface CreateNotificationResponse extends CreateResponse<Notification> {
  data: Notification;
  notificationId: string;
  estimatedDelivery: string;
  deliveryChannels: DeliveryChannel[];
}

// Notification Retrieval APIs
export interface GetNotificationsRequest extends ListRequest {
  recipientId?: string;
  status?: NotificationStatus[];
  priority?: NotificationPriority[];
  channels?: string[];
  read?: boolean;
  timeRange?: NotificationTimeRange;
}

export interface GetNotificationsResponse extends ListResponse<Notification> {
  data: Notification[];
  unreadCount: number;
  priorityCounts: PriorityCount[];
  channelStats: ChannelStats[];
}

// Notification Management APIs
export interface MarkNotificationReadRequest extends BaseApiRequest {
  notificationId: string;
  readBy: string;
  readAt?: string;
  context: MultiTenantContext;
}

export interface MarkNotificationReadResponse extends BaseApiResponse<NotificationRead> {
  data: NotificationRead;
  readAt: string;
  remainingUnread: number;
}

// Supporting Types for Notification Management
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

export interface NotificationContent {
  subject?: string;
  body: string;
  summary?: string;
  html?: string;
  markdown?: string;
  variables?: Record<string, any>;
  template?: NotificationTemplate;
  attachments?: NotificationAttachment[];
  media?: NotificationMedia[];
}

export interface NotificationRecipient {
  id: string;
  type: RecipientType;
  address: string;
  name?: string;
  preferences?: RecipientPreferences;
  groups?: string[];
  roles?: string[];
  conditions?: RecipientCondition[];
  substitutions?: Record<string, any>;
}

export interface NotificationChannel {
  type: ChannelType;
  enabled: boolean;
  configuration: ChannelConfiguration;
  priority: number;
  fallback?: boolean;
  conditions?: ChannelCondition[];
  limits?: ChannelLimits;
}

export interface NotificationScheduling {
  immediate: boolean;
  scheduledAt?: string;
  timezone?: string;
  recurring?: RecurringSchedule;
  delay?: ScheduleDelay;
  conditions?: SchedulingCondition[];
  optimization?: SchedulingOptimization;
}

export interface NotificationDelivery {
  status: DeliveryStatus;
  attempts: DeliveryAttempt[];
  results: DeliveryResult[];
  metrics: DeliveryMetrics;
  errors: DeliveryError[];
  tracking: DeliveryTracking;
}

export interface NotificationTracking {
  trackOpens: boolean;
  trackClicks: boolean;
  trackConversions: boolean;
  utm_parameters?: UtmParameters;
  custom_properties?: Record<string, any>;
  events: TrackingEvent[];
}

export interface NotificationRead {
  notificationId: string;
  recipientId: string;
  readAt: string;
  readBy: string;
  channel: ChannelType;
  device?: DeviceInfo;
  location?: GeoLocation;
  metadata: Record<string, any>;
}

export interface DeliveryChannel {
  type: ChannelType;
  status: ChannelStatus;
  estimatedDelivery: string;
  configuration: ChannelConfiguration;
  limits: ChannelLimits;
}

export interface PriorityCount {
  priority: NotificationPriority;
  count: number;
  unread: number;
  percentage: number;
}

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

// Template Management Types
export interface NotificationTemplate {
  id: string;
  name: string;
  description?: string;
  type: TemplateType;
  category: TemplateCategory;
  content: TemplateContent;
  variables: TemplateVariable[];
  channels: ChannelTemplate[];
  version: string;
  status: TemplateStatus;
  tags: string[];
  metadata: TemplateMetadata;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export interface TemplateContent {
  subject?: string;
  body: string;
  html?: string;
  markdown?: string;
  sms?: string;
  push?: PushTemplateContent;
  in_app?: InAppTemplateContent;
  voice?: VoiceTemplateContent;
}

export interface TemplateVariable {
  name: string;
  type: VariableType;
  required: boolean;
  default_value?: any;
  validation?: VariableValidation;
  description?: string;
  examples?: any[];
}

export interface ChannelTemplate {
  channel: ChannelType;
  content: TemplateContent;
  configuration: ChannelConfiguration;
  enabled: boolean;
  fallback_order?: number;
}

// Enums and Supporting Types
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent' | 'critical';

export type NotificationStatus = 'draft' | 'pending' | 'sent' | 'delivered' | 'read' | 'failed' | 'cancelled';

export type NotificationType = 
  | 'info' | 'success' | 'warning' | 'error' | 'alert' | 'reminder' | 'update' 
  | 'invitation' | 'approval' | 'marketing' | 'transactional' | 'system';

export type NotificationCategory = 
  | 'user_activity' | 'system_event' | 'security' | 'billing' | 'engagement' 
  | 'marketing' | 'support' | 'compliance' | 'maintenance' | 'emergency';

export type NotificationSource = 
  | 'user_action' | 'system_trigger' | 'scheduled_job' | 'webhook' | 'api' 
  | 'manual' | 'automated_rule' | 'monitoring' | 'integration';

export type RecipientType = 'user' | 'group' | 'role' | 'email' | 'phone' | 'device' | 'webhook';

export type ChannelType = 
  | 'email' | 'sms' | 'push' | 'in_app' | 'slack' | 'teams' | 'webhook' 
  | 'voice' | 'whatsapp' | 'telegram' | 'discord' | 'custom';

export type DeliveryStatus = 
  | 'pending' | 'queued' | 'processing' | 'sent' | 'delivered' | 'bounced' 
  | 'failed' | 'rejected' | 'cancelled' | 'expired';

export type ChannelStatus = 'active' | 'inactive' | 'suspended' | 'error' | 'rate_limited';

export type TemplateType = 'system' | 'custom' | 'marketing' | 'transactional' | 'automated';

export type TemplateCategory = 
  | 'welcome' | 'confirmation' | 'alert' | 'reminder' | 'invoice' | 'report' 
  | 'announcement' | 'invitation' | 'password_reset' | 'verification';

export type TemplateStatus = 'draft' | 'active' | 'inactive' | 'archived' | 'deprecated';

export type VariableType = 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object' | 'html';

// Complex Supporting Interfaces
export interface NotificationTimeRange {
  start: string;
  end: string;
  timezone?: string;
}

export interface NotificationMetadata {
  correlation_id?: string;
  campaign_id?: string;
  engagement_id?: string;
  client_account_id?: string;
  tags: string[];
  custom_properties: Record<string, any>;
  source_system?: string;
  version: string;
}

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

export interface RecipientPreferences {
  channels: ChannelPreference[];
  frequency: FrequencyPreference;
  categories: CategoryPreference[];
  quiet_hours?: QuietHours;
  timezone?: string;
  language?: string;
}

export interface RecipientCondition {
  type: ConditionType;
  operator: ConditionOperator;
  value: any;
  metadata?: Record<string, any>;
}

export interface ChannelConfiguration {
  provider?: string;
  credentials?: Record<string, any>;
  settings: Record<string, any>;
  rate_limits?: RateLimit[];
  retry_policy?: RetryPolicy;
  fallback_channel?: ChannelType;
}

export interface ChannelCondition {
  type: ConditionType;
  field: string;
  operator: ConditionOperator;
  value: any;
}

export interface ChannelLimits {
  rate_limit: RateLimit;
  daily_limit?: number;
  monthly_limit?: number;
  concurrent_limit?: number;
  size_limit?: number;
}

export interface RecurringSchedule {
  frequency: ScheduleFrequency;
  interval: number;
  days_of_week?: number[];
  days_of_month?: number[];
  months?: number[];
  end_date?: string;
  max_occurrences?: number;
}

export interface ScheduleDelay {
  amount: number;
  unit: DelayUnit;
  condition?: DelayCondition;
}

export interface SchedulingCondition {
  type: ConditionType;
  operator: ConditionOperator;
  value: any;
}

export interface SchedulingOptimization {
  optimize_for: OptimizationGoal;
  respect_quiet_hours: boolean;
  timezone_optimization: boolean;
  frequency_capping: boolean;
  send_time_optimization: boolean;
}

export interface DeliveryAttempt {
  attempt_number: number;
  channel: ChannelType;
  status: DeliveryStatus;
  attempted_at: string;
  completed_at?: string;
  error?: DeliveryError;
  metadata: Record<string, any>;
}

export interface DeliveryResult {
  channel: ChannelType;
  recipient_id: string;
  status: DeliveryStatus;
  delivered_at?: string;
  message_id?: string;
  provider_response?: Record<string, any>;
  tracking_id?: string;
}

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

export interface DeliveryError {
  code: string;
  message: string;
  category: ErrorCategory;
  retry_after?: number;
  permanent: boolean;
  provider_error?: Record<string, any>;
}

export interface DeliveryTracking {
  tracking_id: string;
  pixel_url?: string;
  click_tracking_enabled: boolean;
  open_tracking_enabled: boolean;
  unsubscribe_url?: string;
  preference_center_url?: string;
}

export interface UtmParameters {
  source?: string;
  medium?: string;
  campaign?: string;
  term?: string;
  content?: string;
  custom?: Record<string, string>;
}

export interface TrackingEvent {
  event_type: TrackingEventType;
  timestamp: string;
  recipient_id: string;
  channel: ChannelType;
  metadata: Record<string, any>;
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

export interface PushTemplateContent {
  title: string;
  body: string;
  icon?: string;
  image?: string;
  badge?: string;
  sound?: string;
  actions?: PushAction[];
  data?: Record<string, any>;
}

export interface InAppTemplateContent {
  title?: string;
  message: string;
  type: InAppNotificationType;
  duration?: number;
  actions?: InAppAction[];
  styling?: InAppStyling;
}

export interface VoiceTemplateContent {
  message: string;
  voice?: VoiceSettings;
  speed?: number;
  volume?: number;
  language?: string;
}

export interface TemplateMetadata {
  author: string;
  version_notes?: string;
  approval_status?: ApprovalStatus;
  approved_by?: string;
  approved_at?: string;
  usage_count: number;
  performance_metrics?: TemplatePerformance;
  tags: string[];
}

export interface VariableValidation {
  min_length?: number;
  max_length?: number;
  pattern?: string;
  allowed_values?: any[];
  required_format?: string;
}

// Additional Enums and Types
export type ActionStyle = 'primary' | 'secondary' | 'danger' | 'success' | 'warning' | 'link';

export type ConditionType = 
  | 'user_property' | 'time_based' | 'location' | 'device' | 'behavior' | 'preference' | 'custom';

export type ConditionOperator = 
  | 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'greater_than' | 'less_than' 
  | 'in' | 'not_in' | 'exists' | 'not_exists' | 'matches' | 'starts_with' | 'ends_with';

export type ScheduleFrequency = 'minutely' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly';

export type DelayUnit = 'minutes' | 'hours' | 'days' | 'weeks' | 'months';

export type OptimizationGoal = 'delivery_rate' | 'open_rate' | 'click_rate' | 'conversion_rate' | 'engagement';

export type ErrorCategory = 'temporary' | 'permanent' | 'rate_limit' | 'authentication' | 'configuration';

export type TrackingEventType = 'sent' | 'delivered' | 'opened' | 'clicked' | 'converted' | 'unsubscribed' | 'bounced';

export type MediaType = 'image' | 'video' | 'audio' | 'document' | 'gif' | 'svg';

export type InAppNotificationType = 'banner' | 'modal' | 'toast' | 'sidebar' | 'overlay' | 'badge';

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'needs_review';

// Additional Supporting Interfaces
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

export interface QuietHours {
  enabled: boolean;
  start_time: string;
  end_time: string;
  timezone: string;
  days: number[];
}

export interface RateLimit {
  requests: number;
  period: string;
  unit: RateLimitUnit;
}

export interface RetryPolicy {
  max_attempts: number;
  initial_delay: number;
  max_delay: number;
  backoff_multiplier: number;
  retry_on: string[];
}

export interface ActionTracking {
  track_clicks: boolean;
  utm_parameters?: UtmParameters;
  custom_properties?: Record<string, any>;
}

export interface DelayCondition {
  type: ConditionType;
  operator: ConditionOperator;
  value: any;
}

export interface MediaDimensions {
  width: number;
  height: number;
}

export interface PushAction {
  id: string;
  title: string;
  icon?: string;
  action?: string;
  input?: PushActionInput;
}

export interface InAppAction {
  id: string;
  label: string;
  action: string;
  style: ActionStyle;
  url?: string;
}

export interface InAppStyling {
  theme: string;
  position: InAppPosition;
  animation?: string;
  custom_css?: string;
}

export interface VoiceSettings {
  name: string;
  gender: VoiceGender;
  language: string;
  accent?: string;
}

export interface TemplatePerformance {
  usage_count: number;
  delivery_rate: number;
  open_rate?: number;
  click_rate?: number;
  conversion_rate?: number;
  last_used: string;
}

export interface DeviceInfo {
  type: DeviceType;
  os: string;
  browser?: string;
  version?: string;
  fingerprint?: string;
}

export interface GeoLocation {
  country: string;
  region: string;
  city: string;
  latitude?: number;
  longitude?: number;
  timezone: string;
}

export type DigestFrequency = 'hourly' | 'daily' | 'weekly' | 'monthly';
export type RateLimitUnit = 'second' | 'minute' | 'hour' | 'day';
export type InAppPosition = 'top' | 'bottom' | 'center' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
export type VoiceGender = 'male' | 'female' | 'neutral';
export type DeviceType = 'desktop' | 'mobile' | 'tablet' | 'tv' | 'watch' | 'speaker' | 'other';

export interface PushActionInput {
  type: InputType;
  placeholder?: string;
  required?: boolean;
}

export type InputType = 'text' | 'number' | 'email' | 'phone' | 'url' | 'password';