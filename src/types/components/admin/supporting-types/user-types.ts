/**
 * User Types
 * 
 * User-related type definitions including user profiles, preferences,
 * and notification settings.
 */

import type { ReactNode } from 'react';

// Base user and role types
export interface User {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  avatar?: string;
  status: UserStatus;
  roles: Role[];
  permissions: Permission[];
  lastLogin?: string;
  loginCount: number;
  failedLoginAttempts: number;
  accountLocked: boolean;
  emailVerified: boolean;
  phoneVerified: boolean;
  mfaEnabled: boolean;
  profile: UserProfile;
  preferences: UserPreferences;
  metadata?: Record<string, string | number | boolean | null>;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface UserProfile {
  title?: string;
  department?: string;
  location?: string;
  timezone?: string;
  language?: string;
  phone?: string;
  address?: Address;
  socialLinks?: SocialLink[];
  bio?: string;
  skills?: string[];
  certifications?: Certification[];
  emergencyContact?: EmergencyContact;
}

export interface Address {
  street1: string;
  street2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface SocialLink {
  platform: string;
  url: string;
  verified: boolean;
}

export interface Certification {
  name: string;
  issuer: string;
  issuedAt: string;
  expiresAt?: string;
  credentialId?: string;
  url?: string;
}

export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
  email?: string;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  dateFormat: string;
  timeFormat: '12h' | '24h';
  numberFormat: string;
  currency: string;
  notifications: NotificationPreferences;
  privacy: PrivacyPreferences;
  display: DisplayPreferences;
  accessibility: AccessibilityPreferences;
}

export interface NotificationPreferences {
  email: EmailNotifications;
  push: PushNotifications;
  sms: SmsNotifications;
  inApp: InAppNotifications;
  digest: DigestNotifications;
}

export interface EmailNotifications {
  enabled: boolean;
  frequency: NotificationFrequency;
  types: EmailNotificationType[];
  quietHours: QuietHours;
}

export interface PushNotifications {
  enabled: boolean;
  frequency: NotificationFrequency;
  types: PushNotificationType[];
  quietHours: QuietHours;
  sound: boolean;
  vibration: boolean;
}

export interface SmsNotifications {
  enabled: boolean;
  types: SmsNotificationType[];
  emergencyOnly: boolean;
}

export interface InAppNotifications {
  enabled: boolean;
  showDesktop: boolean;
  showMobile: boolean;
  duration: number;
  position: NotificationPosition;
}

export interface DigestNotifications {
  enabled: boolean;
  frequency: DigestFrequency;
  day: number;
  time: string;
  includeMetrics: boolean;
  includeSummary: boolean;
}

export interface QuietHours {
  enabled: boolean;
  start: string;
  end: string;
  timezone: string;
}

export interface PrivacyPreferences {
  showProfile: boolean;
  showActivity: boolean;
  showOnlineStatus: boolean;
  allowMessaging: boolean;
  allowDataExport: boolean;
  allowDataDeletion: boolean;
  trackingConsent: TrackingConsent;
}

export interface TrackingConsent {
  analytics: boolean;
  marketing: boolean;
  functional: boolean;
  performance: boolean;
  social: boolean;
}

export interface DisplayPreferences {
  density: 'compact' | 'normal' | 'comfortable';
  sidebarCollapsed: boolean;
  tablePageSize: number;
  showAvatars: boolean;
  showTooltips: boolean;
  showAnimations: boolean;
  showRichText: boolean;
  fontSize: FontSize;
  contrast: ContrastLevel;
}

export interface AccessibilityPreferences {
  screenReader: boolean;
  highContrast: boolean;
  largeText: boolean;
  reducedMotion: boolean;
  keyboardNavigation: boolean;
  voiceControl: boolean;
  colorBlind: ColorBlindnessType;
  alternativeText: boolean;
}

export interface UserActivity {
  id: string;
  userId: string;
  sessionId?: string;
  type: ActivityType;
  action: string;
  resource?: string;
  details?: string;
  data?: Record<string, string | number | boolean | null>;
  duration?: number;
  ipAddress?: string;
  userAgent?: string;
  timestamp: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface UserMetrics {
  active: number;
  sessions: number;
  concurrent: number;
  newUsers: number;
  returningUsers: number;
}

// Role type import from role-permission-types
export interface Role {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  type: RoleType;
  permissions: Permission[];
  hierarchy: number;
  isDefault: boolean;
  isSystem: boolean;
  isActive: boolean;
  conditions?: RoleCondition[];
  metadata?: Record<string, string | number | boolean | null>;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

// Permission type import from role-permission-types
export interface Permission {
  id: string;
  name: string;
  displayName: string;
  description?: string;
  resource: string;
  action: string;
  scope?: PermissionScope;
  conditions?: PermissionCondition[];
  granted: boolean;
  inherited?: boolean;
  source?: string;
  metadata?: Record<string, string | number | boolean | null>;
}

// Supporting types from role-permission-types
export interface RoleCondition {
  type: ConditionType;
  field: string;
  operator: ConditionOperator;
  value: unknown;
  description?: string;
}

export interface PermissionCondition {
  type: ConditionType;
  field: string;
  operator: ConditionOperator;
  value: unknown;
  description?: string;
}

export interface PermissionScope {
  type: ScopeType;
  value: string;
  description?: string;
}

// Enum and union types
export type UserStatus = 'active' | 'inactive' | 'pending' | 'blocked' | 'suspended' | 'archived';
export type RoleType = 'system' | 'custom' | 'temporary' | 'inherited';
export type ConditionType = 'time' | 'location' | 'device' | 'ip' | 'attribute' | 'custom';
export type ConditionOperator = 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'between';
export type ScopeType = 'global' | 'organization' | 'department' | 'team' | 'personal' | 'resource';
export type ActivityType = 'navigation' | 'interaction' | 'api_call' | 'data_access' | 'configuration' | 'authentication' | 'security' | 'system';
export type NotificationFrequency = 'immediate' | 'hourly' | 'daily' | 'weekly' | 'monthly';
export type EmailNotificationType = 'welcome' | 'security' | 'system' | 'reminders' | 'updates' | 'marketing';
export type PushNotificationType = 'alerts' | 'messages' | 'updates' | 'reminders' | 'security';
export type SmsNotificationType = 'security' | 'alerts' | 'verification' | 'emergency';
export type DigestFrequency = 'daily' | 'weekly' | 'monthly';
export type NotificationPosition = 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'center';
export type FontSize = 'small' | 'medium' | 'large' | 'extra-large';
export type ContrastLevel = 'normal' | 'high' | 'highest';
export type ColorBlindnessType = 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia' | 'achromatopsia';