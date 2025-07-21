/**
 * Audit Log Types
 * 
 * Core audit log data structures and related types.
 * 
 * Generated with CC for modular admin type organization.
 */

import { 
  AuditMetadata, 
  GeoLocation, 
  DeviceInfo,
  Environment,
  SessionType,
  AuthenticationMethod,
  BusinessImpact,
  TechnicalImpact,
  DataSensitivity,
  ChangeType
} from '../common';
import { 
  AuditSeverity, 
  AuditAction, 
  AuditResource, 
  AuditOutcome,
  AuditSource
} from './enums';

// Core audit log structure
export interface AuditLog {
  id: string;
  timestamp: string;
  userId?: string;
  sessionId?: string;
  action: AuditAction;
  resource: AuditResource;
  resourceId?: string;
  clientAccountId?: string;
  engagementId?: string;
  severity: AuditSeverity;
  outcome: AuditOutcome;
  details: AuditDetails;
  metadata: AuditMetadata;
  ipAddress?: string;
  userAgent?: string;
  location?: GeoLocation;
  deviceInfo?: DeviceInfo;
  context: AuditContext;
}

// Audit log data for creation
export interface AuditLogData {
  action: AuditAction;
  resource: AuditResource;
  resourceId?: string;
  clientAccountId?: string;
  engagementId?: string;
  outcome: AuditOutcome;
  details: AuditDetails;
  metadata?: Record<string, any>;
  context?: AuditContext;
}

// Audit details
export interface AuditDetails {
  description: string;
  changes?: FieldChange[];
  errors?: AuditError[];
  duration?: number;
  dataVolume?: DataVolume;
  impact?: ImpactAssessment;
  compliance?: ComplianceContext;
}

// Audit context
export interface AuditContext {
  tenant_id?: string;
  organization_id?: string;
  department?: string;
  project?: string;
  environment: Environment;
  session_type?: SessionType;
  authentication_method?: AuthenticationMethod;
  permissions?: string[];
  risk_score?: number;
}

// Field change tracking
export interface FieldChange {
  field: string;
  old_value: any;
  new_value: any;
  change_type: ChangeType;
  sensitive: boolean;
}

// Audit error information
export interface AuditError {
  code: string;
  message: string;
  details?: string;
  stack_trace?: string;
}

// Data volume metrics
export interface DataVolume {
  records: number;
  size_bytes: number;
  affected_tables?: string[];
  query_complexity?: number;
}

// Impact assessment
export interface ImpactAssessment {
  users_affected: number;
  accounts_affected: number;
  data_sensitivity: DataSensitivity;
  business_impact: BusinessImpact;
  technical_impact: TechnicalImpact;
}

// Compliance context
export interface ComplianceContext {
  frameworks: string[];
  requirements: string[];
  controls: string[];
  exceptions: ComplianceException[];
}

// Compliance exception
export interface ComplianceException {
  exception_id: string;
  reason: string;
  approved_by: string;
  expires_at?: string;
}

// Action summary for analytics
export interface ActionSummary {
  action: AuditAction;
  count: number;
  unique_users: number;
  success_rate: number;
  average_duration: number;
  risk_distribution: RiskDistribution;
  trend: TrendInfo;
}

// Risk distribution
export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

// Trend information
export interface TrendInfo {
  direction: TrendDirection;
  rate: number;
  prediction: TrendPrediction;
}

// Trend prediction
export interface TrendPrediction {
  next_period: number;
  confidence: ConfidenceLevel;
  factors: string[];
}

// Import common types
type TrendDirection = import('../common').TrendDirection;
type ConfidenceLevel = import('../common').ConfidenceLevel;