/**
 * Notification Enums
 *
 * Enumeration types specific to notification management.
 *
 * Generated with CC for modular admin type organization.
 */

// Re-export common priority as NotificationPriority
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent' | 'critical';

// Notification status
export type NotificationStatus = 'draft' | 'pending' | 'sent' | 'delivered' | 'read' | 'failed' | 'cancelled';

// Notification types
export type NotificationType =
  | 'info' | 'success' | 'warning' | 'error' | 'alert' | 'reminder' | 'update'
  | 'invitation' | 'approval' | 'marketing' | 'transactional' | 'system';

// Notification categories
export type NotificationCategory =
  | 'user_activity' | 'system_event' | 'security' | 'billing' | 'engagement'
  | 'marketing' | 'support' | 'compliance' | 'maintenance' | 'emergency';

// Notification sources
export type NotificationSource =
  | 'user_action' | 'system_trigger' | 'scheduled_job' | 'webhook' | 'api'
  | 'manual' | 'automated_rule' | 'monitoring' | 'integration';

// Channel types
export type ChannelType =
  | 'email' | 'sms' | 'push' | 'in_app' | 'slack' | 'teams' | 'webhook'
  | 'voice' | 'whatsapp' | 'telegram' | 'discord' | 'custom';

// Delivery status
export type DeliveryStatus =
  | 'pending' | 'queued' | 'processing' | 'sent' | 'delivered' | 'bounced'
  | 'failed' | 'rejected' | 'cancelled' | 'expired';

// Template types
export type TemplateType = 'system' | 'custom' | 'marketing' | 'transactional' | 'automated';

// Template categories
export type TemplateCategory =
  | 'welcome' | 'confirmation' | 'alert' | 'reminder' | 'invoice' | 'report'
  | 'announcement' | 'invitation' | 'password_reset' | 'verification';

// Template status
export type TemplateStatus = 'draft' | 'active' | 'inactive' | 'archived' | 'deprecated';

// Variable types
export type VariableType = 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object' | 'html';

// Error categories
export type ErrorCategory = 'temporary' | 'permanent' | 'rate_limit' | 'authentication' | 'configuration';

// Tracking event types
export type TrackingEventType = 'sent' | 'delivered' | 'opened' | 'clicked' | 'converted' | 'unsubscribed' | 'bounced';
