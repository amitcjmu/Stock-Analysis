/**
 * Notification Template Types
 * 
 * Types for notification template management and customization.
 * 
 * Generated with CC for modular admin type organization.
 */

import { TemplateMetadata } from '../common';
import { 
  TemplateType, 
  TemplateCategory, 
  TemplateStatus, 
  VariableType,
  ChannelType 
} from './enums';

// Full notification template
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

// Template content for different channels
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

// Template variable definition
export interface TemplateVariable {
  name: string;
  type: VariableType;
  required: boolean;
  default_value?: any;
  validation?: VariableValidation;
  description?: string;
  examples?: any[];
}

// Channel-specific template configuration
export interface ChannelTemplate {
  channel: ChannelType;
  content: TemplateContent;
  configuration: ChannelConfiguration;
  enabled: boolean;
  fallback_order?: number;
}

// Push notification template content
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

// In-app notification template content
export interface InAppTemplateContent {
  title?: string;
  message: string;
  type: InAppNotificationType;
  duration?: number;
  actions?: InAppAction[];
  styling?: InAppStyling;
}

// Voice notification template content
export interface VoiceTemplateContent {
  message: string;
  voice?: VoiceSettings;
  speed?: number;
  volume?: number;
  language?: string;
}

// Variable validation rules
export interface VariableValidation {
  min_length?: number;
  max_length?: number;
  pattern?: string;
  allowed_values?: any[];
  required_format?: string;
}

// Push notification action
export interface PushAction {
  id: string;
  title: string;
  icon?: string;
  action?: string;
  input?: PushActionInput;
}

// In-app notification action
export interface InAppAction {
  id: string;
  label: string;
  action: string;
  style: ActionStyle;
  url?: string;
}

// In-app notification styling
export interface InAppStyling {
  theme: string;
  position: InAppPosition;
  animation?: string;
  custom_css?: string;
}

// Voice settings
export interface VoiceSettings {
  name: string;
  gender: VoiceGender;
  language: string;
  accent?: string;
}

// Push action input configuration
export interface PushActionInput {
  type: InputType;
  placeholder?: string;
  required?: boolean;
}

// Template performance metrics
export interface TemplatePerformance {
  usage_count: number;
  delivery_rate: number;
  open_rate?: number;
  click_rate?: number;
  conversion_rate?: number;
  last_used: string;
}

// Import necessary types
type ChannelConfiguration = import('./notification').ChannelConfiguration;
type ActionStyle = import('./notification').ActionStyle;

// Enums and types
export type InAppNotificationType = 'banner' | 'modal' | 'toast' | 'sidebar' | 'overlay' | 'badge';
export type InAppPosition = 'top' | 'bottom' | 'center' | 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
export type VoiceGender = 'male' | 'female' | 'neutral';
export type InputType = 'text' | 'number' | 'email' | 'phone' | 'url' | 'password';