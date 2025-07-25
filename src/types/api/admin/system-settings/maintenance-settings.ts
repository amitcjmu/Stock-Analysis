/**
 * Maintenance Settings Configuration Types
 *
 * System maintenance configuration including maintenance windows,
 * automation, backup settings, and update procedures.
 *
 * Generated with CC for modular admin type organization.
 */

// Maintenance Settings Configuration
export interface MaintenanceSettings {
  windows: MaintenanceWindow[];
  notifications: MaintenanceNotificationConfig;
  automation: MaintenanceAutomationConfig;
  backup: BackupConfig;
  updates: UpdateConfig;
  monitoring: MaintenanceMonitoringConfig;
}

export interface MaintenanceWindow {
  id: string;
  name: string;
  startTime: string;
  endTime: string;
  recurring: boolean;
  timezone: string;
}

export interface MaintenanceNotificationConfig {
  enabled: boolean;
  channels: string[];
  advanceNotice: number;
}

export interface MaintenanceAutomationConfig {
  enabled: boolean;
  scripts: string[];
  rollback: boolean;
}

export interface BackupConfig {
  enabled: boolean;
  frequency: string;
  retention: number;
}

export interface UpdateConfig {
  autoUpdate: boolean;
  schedule: string;
  rollback: boolean;
}

export interface MaintenanceMonitoringConfig {
  enabled: boolean;
  metrics: string[];
  alerts: boolean;
}
