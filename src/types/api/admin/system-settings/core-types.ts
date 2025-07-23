/**
 * System Settings Core Types
 * 
 * Core system settings interfaces and fundamental data structures.
 * 
 * Generated with CC for modular admin type organization.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  GetRequest,
  GetResponse,
  UpdateRequest,
  UpdateResponse
} from '../../shared';
import type { ConfigurationValue } from '../../../shared/config-types';

// System Settings APIs
export interface GetSystemSettingsRequest extends GetRequest {
  category?: SettingCategory;
  includeDefaults?: boolean;
  includeDescription?: boolean;
  includeValidation?: boolean;
}

export interface GetSystemSettingsResponse extends GetResponse<SystemSettings> {
  data: SystemSettings;
  categories: SettingCategoryDetails[];
  validation: SettingValidation[];
  dependencies: SettingDependency[];
}

export interface UpdateSystemSettingsRequest extends UpdateRequest<Partial<SystemSettingsData>> {
  data: Partial<SystemSettingsData>;
  category?: string;
  validateChanges?: boolean;
  notifyAdmins?: boolean;
  scheduleRestart?: boolean;
}

export interface UpdateSystemSettingsResponse extends UpdateResponse<SystemSettings> {
  data: SystemSettings;
  validationResults: SettingValidationResult[];
  changesApplied: SettingChange[];
  restartRequired: boolean;
}

// Core Settings Types
export interface SystemSettings {
  id: string;
  version: string;
  lastUpdated: string;
  updatedBy: string;
  security: SecuritySettings;
  integration: IntegrationSettings;
  notification: NotificationSettings;
  performance: PerformanceSettings;
  compliance: ComplianceSettings;
  features: FeatureSettings;
  maintenance: MaintenanceSettings;
  monitoring: MonitoringSettings;
}

export interface SystemSettingsData {
  security?: Partial<SecuritySettings>;
  integration?: Partial<IntegrationSettings>;
  notification?: Partial<NotificationSettings>;
  performance?: Partial<PerformanceSettings>;
  compliance?: Partial<ComplianceSettings>;
  features?: Partial<FeatureSettings>;
  maintenance?: Partial<MaintenanceSettings>;
  monitoring?: Partial<MonitoringSettings>;
}

export interface SettingCategoryDetails {
  category: SettingCategory;
  name: string;
  description: string;
  settings: Setting[];
  permissions: string[];
  validation: CategoryValidation;
}

export interface Setting {
  key: string;
  name: string;
  description: string;
  type: SettingType;
  value: ConfigurationValue;
  defaultValue: ConfigurationValue;
  required: boolean;
  validation: SettingValidationRule[];
  dependencies: string[];
  sensitive: boolean;
  restartRequired: boolean;
  metadata: Record<string, ConfigurationValue>;
}

export interface SettingValidation {
  key: string;
  rules: SettingValidationRule[];
  dependencies: SettingDependency[];
  warnings: string[];
  errors: string[];
}

export interface SettingValidationRule {
  type: ValidationType;
  value?: ConfigurationValue;
  message: string;
  severity: ValidationSeverity;
}

export interface SettingDependency {
  setting: string;
  dependsOn: string[];
  condition: DependencyCondition;
  message: string;
}

export interface SettingValidationResult {
  setting: string;
  valid: boolean;
  warnings: ValidationMessage[];
  errors: ValidationMessage[];
  suggestions: string[];
}

export interface SettingChange {
  setting: string;
  oldValue: ConfigurationValue;
  newValue: ConfigurationValue;
  appliedAt: string;
  appliedBy: string;
  impact: ChangeImpact;
  rollbackAvailable: boolean;
}

// Enums and Supporting Types
export type SettingCategory = 
  | 'security' 
  | 'integration' 
  | 'notification' 
  | 'performance' 
  | 'compliance' 
  | 'features' 
  | 'maintenance' 
  | 'monitoring';

export type SettingType = 
  | 'string' 
  | 'number' 
  | 'boolean' 
  | 'array' 
  | 'object' 
  | 'enum' 
  | 'json' 
  | 'secret';

export type ValidationType = 
  | 'required' 
  | 'min' 
  | 'max' 
  | 'pattern' 
  | 'enum' 
  | 'custom' 
  | 'dependency';

export type ValidationSeverity = 'info' | 'warning' | 'error' | 'critical';

export type DependencyCondition = 
  | 'equals' 
  | 'not_equals' 
  | 'greater_than' 
  | 'less_than' 
  | 'contains' 
  | 'enabled' 
  | 'disabled';

export type ChangeImpact = 'none' | 'low' | 'medium' | 'high' | 'critical';

// Supporting Complex Interfaces
export interface CategoryValidation {
  required: string[];
  optional: string[];
  dependencies: Record<string, string[]>;
  conflicts: Record<string, string[]>;
}

export interface ValidationMessage {
  message: string;
  field?: string;
  severity: ValidationSeverity;
  code?: string;
}

// Re-export specific setting types (defined in other modules)
export type {
  SecuritySettings
} from './security-settings';

export type {
  IntegrationSettings
} from './integration-settings';

export type {
  NotificationSettings
} from './notification-settings';

export type {
  PerformanceSettings
} from './performance-settings';

export type {
  ComplianceSettings
} from './compliance-settings';

export type {
  FeatureSettings
} from './feature-settings';

export type {
  MaintenanceSettings
} from './maintenance-settings';

export type {
  MonitoringSettings
} from './monitoring-settings';