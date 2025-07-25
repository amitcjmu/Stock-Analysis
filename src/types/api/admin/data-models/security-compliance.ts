/**
 * Security and Compliance Types
 *
 * Security settings, audit trails, compliance frameworks,
 * and regulatory compliance management types.
 *
 * Generated with CC for modular admin type organization.
 */

import type { GeographicCoordinates } from './base-entities';
import type { TwoFactorMethod } from './enums';

export interface SecuritySettings {
  twoFactorEnabled: boolean;
  twoFactorMethod?: TwoFactorMethod;
  backupCodes?: string[];
  trustedDevices: TrustedDevice[];
  sessionTimeout: number;
  loginAttempts: number;
  lockedUntil?: string;
  lastPasswordChange: string;
  passwordHistory: PasswordHistoryEntry[];
  ipWhitelist?: string[];
  locationTracking: boolean;
  deviceTracking: boolean;
}

export interface TrustedDevice {
  deviceId: string;
  name: string;
  type: DeviceType;
  fingerprint: string;
  firstSeen: string;
  lastSeen: string;
  trusted: boolean;
  location?: GeographicCoordinates;
  userAgent: string;
}

export interface PasswordHistoryEntry {
  hashedPassword: string;
  changedAt: string;
  strength: PasswordStrength;
  method: PasswordChangeMethod;
}

// Compliance Framework Types
export interface ComplianceFramework {
  id: string;
  name: string;
  version: string;
  description: string;
  requirements: ComplianceRequirement[];
  controls: ComplianceControl[];
  assessments: ComplianceAssessment[];
  status: ComplianceFrameworkStatus;
}

export interface ComplianceRequirement {
  id: string;
  framework: string;
  section: string;
  title: string;
  description: string;
  mandatory: boolean;
  controls: string[];
  evidence: ComplianceEvidence[];
  status: ComplianceRequirementStatus;
}

export interface ComplianceControl {
  id: string;
  name: string;
  description: string;
  type: ControlType;
  frequency: ControlFrequency;
  owner: string;
  automated: boolean;
  evidence_required: EvidenceType[];
  last_tested?: string;
  status: ControlStatus;
}

export interface ComplianceAssessment {
  id: string;
  framework: string;
  assessor: string;
  assessment_date: string;
  scope: string[];
  findings: AssessmentFinding[];
  recommendations: AssessmentRecommendation[];
  score: number;
  status: AssessmentStatus;
}

export interface ComplianceEvidence {
  type: EvidenceType;
  description: string;
  location: string;
  collected_at: string;
  collected_by: string;
  hash?: string;
  verified: boolean;
}

// Supporting compliance interfaces
export interface AssessmentFinding {
  id: string;
  severity: FindingSeverity;
  category: string;
  description: string;
  evidence: string[];
  recommendations: string[];
  status: FindingStatus;
  assignedTo?: string;
  dueDate?: string;
}

export interface AssessmentRecommendation {
  id: string;
  priority: RecommendationPriority;
  category: string;
  description: string;
  implementation_guidance: string;
  estimated_effort: string;
  dependencies: string[];
  status: RecommendationStatus;
}

// Security-related enums
export type DeviceType = 'desktop' | 'mobile' | 'tablet' | 'smartwatch' | 'tv' | 'other';
export type PasswordStrength = 'weak' | 'fair' | 'good' | 'strong' | 'very_strong';
export type PasswordChangeMethod = 'user_initiated' | 'admin_reset' | 'forced_expiry' | 'security_incident';
export type ComplianceFrameworkStatus = 'active' | 'deprecated' | 'draft' | 'archived';
export type ComplianceRequirementStatus = 'met' | 'not_met' | 'partial' | 'not_applicable' | 'pending';
export type ControlType = 'preventive' | 'detective' | 'corrective' | 'compensating';
export type ControlFrequency = 'continuous' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annually';
export type ControlStatus = 'effective' | 'ineffective' | 'not_tested' | 'exception' | 'remediation_required';
export type AssessmentStatus = 'planned' | 'in_progress' | 'completed' | 'approved' | 'rejected';
export type EvidenceType = 'document' | 'screenshot' | 'log_file' | 'video' | 'testimony' | 'system_output';
export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'informational';
export type FindingStatus = 'open' | 'in_progress' | 'resolved' | 'accepted_risk' | 'false_positive';
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low';
export type RecommendationStatus = 'pending' | 'in_progress' | 'implemented' | 'deferred' | 'rejected';
