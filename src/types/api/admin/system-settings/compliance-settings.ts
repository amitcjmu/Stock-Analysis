/**
 * Compliance Settings Configuration Types
 * 
 * Compliance and governance configuration including data protection,
 * retention policies, privacy settings, and regulatory frameworks.
 * 
 * Generated with CC for modular admin type organization.
 */

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
  policies: Record<string, any>;
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
  rules: Record<string, any>;
}