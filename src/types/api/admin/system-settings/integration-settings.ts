/**
 * Integration Settings Configuration Types
 *
 * External integration configuration including APIs, webhooks, OAuth,
 * SSO, messaging, and third-party service configurations.
 *
 * Generated with CC for modular admin type organization.
 */

// Integration Settings Configuration
export interface IntegrationSettings {
  apis: ApiIntegrationConfig;
  webhooks: WebhookConfig;
  oauth: OAuthConfig;
  sso: SsoConfig;
  external: ExternalIntegrationConfig;
  messaging: MessagingConfig;
  storage: StorageIntegrationConfig;
  monitoring: MonitoringIntegrationConfig;
}

export interface ApiIntegrationConfig {
  enabled: boolean;
  timeout: number;
  retries: number;
}

export interface WebhookConfig {
  enabled: boolean;
  maxRetries: number;
  timeout: number;
}

export interface OAuthConfig {
  providers: string[];
  redirectUri: string;
  scopes: string[];
}

export interface SsoConfig {
  enabled: boolean;
  provider: string;
  autoProvision: boolean;
}

export interface ExternalIntegrationConfig {
  enabled: boolean;
  providers: Record<string, string | number | boolean | null>;
  timeout: number;
}

export interface MessagingConfig {
  provider: string;
  queues: string[];
  dlq: boolean;
}

export interface StorageIntegrationConfig {
  provider: string;
  bucket: string;
  region: string;
}

export interface MonitoringIntegrationConfig {
  enabled: boolean;
  providers: string[];
  metrics: string[];
}
