/**
 * User Profile and Preferences Types
 * 
 * User-specific configuration, preferences, and settings types.
 * Handles personal customization and user experience configuration.
 * 
 * Generated with CC for modular admin type organization.
 */

import type {
  ContactMethod,
  NotificationCategory,
  TwoFactorMethod,
  VisibilityLevel,
  DayOfWeek
} from './enums';

export interface UserPreferences {
  theme: ThemeType;
  language: string;
  locale: string;
  timezone: string;
  dateFormat: DateFormatType;
  timeFormat: TimeFormatType;
  currency: string;
  numberFormat: NumberFormatType;
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  accessibility: AccessibilityPreferences;
  dashboard: DashboardPreferences;
}

export interface UserSettings {
  security: UserSecuritySettings;
  communication: CommunicationSettings;
  workflow: WorkflowSettings;
  integration: UserIntegrationSettings;
  data: DataSettings;
  billing: UserBillingSettings;
}

export interface NotificationPreferences {
  email: boolean;
  sms: boolean;
  push: boolean;
  inApp: boolean;
  categories: Record<NotificationCategory, boolean>;
  frequency: NotificationFrequency;
  quietHours?: QuietHours;
  digest: DigestSettings;
}

export interface PrivacyPreferences {
  profileVisibility: VisibilityLevel;
  activityTracking: boolean;
  analyticsOptOut: boolean;
  marketingEmails: boolean;
  dataSharing: DataSharingPreference[];
  cookieConsent: CookieConsentStatus;
  thirdPartyIntegrations: boolean;
}

export interface AccessibilityPreferences {
  screenReader: boolean;
  highContrast: boolean;
  largeText: boolean;
  colorBlindSupport: boolean;
  keyboardNavigation: boolean;
  motionReduced: boolean;
  audioDescriptions: boolean;
  closedCaptions: boolean;
}

export interface DashboardPreferences {
  defaultView: string;
  layout: DashboardLayout;
  widgets: WidgetConfiguration[];
  refreshInterval: number;
  autoRefresh: boolean;
  pinned: string[];
  hidden: string[];
}

export interface UserSecuritySettings {
  twoFactor: TwoFactorSettings;
  sessions: SessionSettings;
  privacy: SecurityPrivacySettings;
  access: AccessSettings;
}

export interface CommunicationSettings {
  channels: CommunicationChannelSettings[];
  preferences: CommunicationPreferences;
  boundaries: CommunicationBoundaries;
}

export interface WorkflowSettings {
  automation: AutomationSettings;
  approvals: ApprovalSettings;
  notifications: WorkflowNotificationSettings;
  integrations: WorkflowIntegrationSettings;
}

// Security and privacy related settings
export interface TwoFactorSettings {
  enabled: boolean;
  method: TwoFactorMethod;
  backupCodes: BackupCodeSettings;
  trustedDevices: TrustedDeviceSettings;
}

export interface SessionSettings {
  timeout: number;
  maxConcurrent: number;
  rememberDevice: boolean;
  logoutOnClose: boolean;
}

export interface SecurityPrivacySettings {
  profileVisibility: VisibilityLevel;
  activityLogging: boolean;
  dataSharing: boolean;
  locationTracking: boolean;
}

export interface AccessSettings {
  ipRestrictions: IpRestriction[];
  timeRestrictions: TimeRestriction[];
  locationRestrictions: LocationRestriction[];
}

// Communication settings
export interface CommunicationChannelSettings {
  channel: ContactMethod;
  enabled: boolean;
  priority: number;
  address: string;
  verified: boolean;
}

export interface CommunicationPreferences {
  defaultChannel: ContactMethod;
  urgentChannel: ContactMethod;
  language: string;
  tone: CommunicationTone;
}

export interface CommunicationBoundaries {
  quietHours: QuietHours;
  doNotDisturb: boolean;
  emergency_override: boolean;
  vacation_mode: boolean;
}

// Supporting preference interfaces
export interface QuietHours {
  enabled: boolean;
  startTime: string;
  endTime: string;
  timezone: string;
  days: DayOfWeek[];
  exceptions: QuietHoursException[];
}

export interface DigestSettings {
  enabled: boolean;
  frequency: DigestFrequency;
  time: string;
  timezone: string;
  categories: NotificationCategory[];
  maxItems: number;
}

export interface DataSharingPreference {
  partner: string;
  dataTypes: string[];
  purpose: string;
  consent: boolean;
  consentDate: string;
  expiryDate?: string;
}

export interface WidgetConfiguration {
  widgetId: string;
  type: WidgetType;
  position: WidgetPosition;
  size: WidgetSize;
  configuration: Record<string, string | number | boolean | null>;
  visible: boolean;
  minimized: boolean;
}

export interface WidgetPosition {
  x: number;
  y: number;
  row?: number;
  column?: number;
}

export interface WidgetSize {
  width: number;
  height: number;
  minWidth?: number;
  minHeight?: number;
  maxWidth?: number;
  maxHeight?: number;
}

export interface QuietHoursException {
  date: string;
  reason: string;
  override: boolean;
}

export interface BackupCodeSettings {
  generated: boolean;
  count: number;
  used: number;
  lastRegenerated?: string;
}

export interface TrustedDeviceSettings {
  enabled: boolean;
  maxDevices: number;
  trustDuration: number;
  requireReauth: boolean;
}

export interface IpRestriction {
  cidr: string;
  description?: string;
  whitelist: boolean;
}

export interface TimeRestriction {
  startTime: string;
  endTime: string;
  days: DayOfWeek[];
  timezone: string;
}

export interface LocationRestriction {
  countries: string[];
  regions?: string[];
  whitelist: boolean;
}

// Placeholder types for complex workflow settings
export type AutomationSettings = Record<string, unknown>; /* automation configuration */
export type ApprovalSettings = Record<string, unknown>; /* approval workflow settings */
export type WorkflowNotificationSettings = Record<string, unknown>; /* workflow notification configuration */
export type WorkflowIntegrationSettings = Record<string, unknown>; /* workflow integration settings */
export type UserIntegrationSettings = Record<string, unknown>; /* user integration preferences */
export type DataSettings = Record<string, unknown>; /* data management settings */
export type UserBillingSettings = Record<string, unknown>; /* user billing preferences */

// User preference enums
export type ThemeType = 'light' | 'dark' | 'auto' | 'high_contrast';
export type DateFormatType = 'MM/DD/YYYY' | 'DD/MM/YYYY' | 'YYYY-MM-DD' | 'DD MMM YYYY';
export type TimeFormatType = '12h' | '24h';
export type NumberFormatType = 'US' | 'EU' | 'UK' | 'IN' | 'custom';
export type NotificationFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly' | 'monthly';
export type CookieConsentStatus = 'necessary' | 'functional' | 'analytics' | 'marketing' | 'all' | 'none';
export type DashboardLayout = 'grid' | 'list' | 'kanban' | 'timeline' | 'custom';
export type DigestFrequency = 'daily' | 'weekly' | 'monthly';
export type WidgetType = 'chart' | 'metric' | 'list' | 'table' | 'calendar' | 'map' | 'feed' | 'custom';
export type CommunicationTone = 'formal' | 'casual' | 'friendly' | 'professional' | 'concise';