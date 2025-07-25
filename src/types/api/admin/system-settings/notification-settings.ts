/**
 * Notification Settings Configuration Types
 *
 * Notification system configuration including email, SMS, push notifications,
 * in-app notifications, and delivery settings.
 *
 * Generated with CC for modular admin type organization.
 */

// Notification Settings Configuration
export interface NotificationSettings {
  email: EmailConfig;
  sms: SmsConfig;
  push: PushConfig;
  inApp: InAppNotificationConfig;
  webhooks: WebhookNotificationConfig;
  channels: NotificationChannelConfig[];
  templates: NotificationTemplateConfig[];
  delivery: DeliveryConfig;
}

export interface EmailConfig {
  provider: string;
  fromAddress: string;
  templates: Record<string, string | number | boolean | null>;
}

export interface SmsConfig {
  provider: string;
  fromNumber: string;
  templates: Record<string, string | number | boolean | null>;
}

export interface PushConfig {
  enabled: boolean;
  providers: string[];
  certificates: Record<string, string | number | boolean | null>;
}

export interface InAppNotificationConfig {
  enabled: boolean;
  retention: number;
  maxPerUser: number;
}

export interface WebhookNotificationConfig {
  enabled: boolean;
  endpoints: string[];
  retries: number;
}

export interface NotificationChannelConfig {
  type: string;
  enabled: boolean;
  configuration: Record<string, string | number | boolean | null>;
}

export interface NotificationTemplateConfig {
  id: string;
  name: string;
  content: Record<string, string | number | boolean | null>;
}

export interface DeliveryConfig {
  maxRetries: number;
  retryDelay: number;
  timeout: number;
}
