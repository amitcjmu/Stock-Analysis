/**
 * Compliance Settings Configuration Types
 *
 * Compliance and governance configuration including data protection,
 * retention policies, privacy settings, and regulatory frameworks.
 *
 * Generated with CC for modular admin type organization.
 */

// Policy and Rule Configuration Types
export interface RetentionPolicy {
  period: number;
  unit: 'days' | 'months' | 'years';
  autoDelete: boolean;
  archiveBeforeDelete: boolean;
  exemptions?: string[];
}

export interface PolicyRule {
  id: string;
  type: 'mandatory' | 'optional' | 'conditional';
  condition?: string;
  action: 'allow' | 'deny' | 'require_approval';
  parameters?: Record<string, string | number | boolean>;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

// Compliance Settings Configuration
export interface ComplianceSettings {
  dataProtection: DataProtectionConfig;
  retention: DataRetentionConfig;
  audit: ComplianceAuditConfig;
  privacy: PrivacyConfig;
  governance: GovernanceConfig;
  frameworks: ComplianceFramework[];
  certifications: CertificationConfig[];
  policies: PolicyConfig[];
}

export interface DataProtectionConfig {
  encryption: boolean;
  anonymization: boolean;
  pseudonymization: boolean;
}

export interface DataRetentionConfig {
  enabled: boolean;
  defaultPeriod: number;
  policies: Record<string, RetentionPolicy>;
}

export interface ComplianceAuditConfig {
  enabled: boolean;
  frequency: string;
  scope: string[];
}

export interface PrivacyConfig {
  consentRequired: boolean;
  rightToErasure: boolean;
  dataPortability: boolean;
}

export interface GovernanceConfig {
  policies: string[];
  enforcement: boolean;
  reporting: boolean;
}

export interface ComplianceFramework {
  name: string;
  version: string;
  applicability: string[];
}

export interface CertificationConfig {
  type: string;
  issuer: string;
  expiryDate: string;
}

export interface PolicyConfig {
  id: string;
  name: string;
  rules: Record<string, PolicyRule>;
}
