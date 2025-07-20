/**
 * Audit and Logging API Types
 * 
 * Type definitions for audit trail management, security event logging,
 * compliance tracking, and system logging operations.
 * 
 * Generated with CC for modular admin type organization.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  ListRequest,
  ListResponse,
  CreateRequest,
  CreateResponse
} from '../shared';

// Audit Log APIs
export interface GetAuditLogsRequest extends ListRequest {
  userId?: string;
  action?: string;
  resource?: string;
  clientAccountId?: string;
  engagementId?: string;
  timeRange?: TimeRange;
  severity?: AuditSeverity[];
  includeDetails?: boolean;
}

export interface GetAuditLogsResponse extends ListResponse<AuditLog> {
  data: AuditLog[];
  actionSummary: ActionSummary[];
  userActivity: UserActivitySummary[];
  securityEvents: SecurityEvent[];
}

export interface CreateAuditLogRequest extends CreateRequest<AuditLogData> {
  data: AuditLogData;
  severity: AuditSeverity;
  automated?: boolean;
  alertRequired?: boolean;
}

export interface CreateAuditLogResponse extends CreateResponse<AuditLog> {
  data: AuditLog;
  logId: string;
  alertTriggered: boolean;
  notificationsSent: string[];
}

// Security Event APIs
export interface GetSecurityEventsRequest extends ListRequest {
  eventTypes?: SecurityEventType[];
  severity?: SecuritySeverity[];
  resolved?: boolean;
  timeRange?: TimeRange;
  includeContext?: boolean;
}

export interface GetSecurityEventsResponse extends ListResponse<SecurityEvent> {
  data: SecurityEvent[];
  threatLevel: ThreatLevel;
  incidentSummary: IncidentSummary;
  recommendations: SecurityRecommendation[];
}

// Supporting Types for Audit and Logging
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

export interface AuditDetails {
  description: string;
  changes?: FieldChange[];
  errors?: AuditError[];
  duration?: number;
  dataVolume?: DataVolume;
  impact?: ImpactAssessment;
  compliance?: ComplianceContext;
}

export interface AuditMetadata {
  source: AuditSource;
  correlation_id?: string;
  request_id?: string;
  trace_id?: string;
  version: string;
  schema_version: string;
  tags: string[];
  custom: Record<string, any>;
}

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

export interface SecurityEvent {
  id: string;
  type: SecurityEventType;
  severity: SecuritySeverity;
  timestamp: string;
  source: SecurityEventSource;
  description: string;
  details: SecurityEventDetails;
  affected_resources: AffectedResource[];
  indicators: SecurityIndicator[];
  mitigation: MitigationInfo;
  investigation: InvestigationInfo;
  resolved: boolean;
  resolved_at?: string;
  resolved_by?: string;
  resolution_notes?: string;
  metadata: SecurityEventMetadata;
}

export interface SecurityEventDetails {
  attack_vector?: string;
  attack_pattern?: string;
  threat_actor?: ThreatActor;
  compromise_assessment: CompromiseAssessment;
  timeline: SecurityTimeline[];
  evidence: Evidence[];
  impact: SecurityImpact;
  confidence: ConfidenceLevel;
}

export interface ActionSummary {
  action: AuditAction;
  count: number;
  unique_users: number;
  success_rate: number;
  average_duration: number;
  risk_distribution: RiskDistribution;
  trend: TrendInfo;
}

export interface UserActivitySummary {
  user_id: string;
  email: string;
  display_name: string;
  total_actions: number;
  unique_resources: number;
  risk_score: number;
  last_activity: string;
  locations: ActivityLocation[];
  devices: ActivityDevice[];
  patterns: ActivityPattern[];
  anomalies: ActivityAnomaly[];
}

export interface IncidentSummary {
  total_incidents: number;
  open_incidents: number;
  critical_incidents: number;
  average_resolution_time: number;
  most_common_types: IncidentTypeCount[];
  trending_threats: TrendingThreat[];
  affected_accounts: number;
  financial_impact?: FinancialImpact;
}

export interface SecurityRecommendation {
  id: string;
  type: RecommendationType;
  priority: RecommendationPriority;
  title: string;
  description: string;
  rationale: string;
  implementation_steps: string[];
  estimated_effort: EffortEstimate;
  risk_reduction: RiskReduction;
  compliance_impact: ComplianceImpact;
  dependencies: string[];
  resources: RecommendationResource[];
}

// Enums and Supporting Types
export type AuditSeverity = 'low' | 'medium' | 'high' | 'critical';

export type AuditAction = 
  | 'login' | 'logout' | 'password_change' | 'password_reset'
  | 'user_create' | 'user_update' | 'user_delete' | 'user_deactivate'
  | 'role_assign' | 'role_revoke' | 'permission_grant' | 'permission_deny'
  | 'account_create' | 'account_update' | 'account_delete' | 'account_suspend'
  | 'engagement_create' | 'engagement_update' | 'engagement_delete'
  | 'data_access' | 'data_export' | 'data_import' | 'data_delete'
  | 'settings_change' | 'integration_add' | 'integration_remove'
  | 'report_generate' | 'report_download' | 'backup_create' | 'backup_restore'
  | 'api_call' | 'webhook_trigger' | 'notification_send'
  | 'security_violation' | 'compliance_check' | 'system_error';

export type AuditResource = 
  | 'user' | 'role' | 'permission' | 'client_account' | 'engagement'
  | 'flow' | 'data' | 'report' | 'setting' | 'integration' | 'notification'
  | 'session' | 'api' | 'webhook' | 'audit_log' | 'system';

export type AuditOutcome = 'success' | 'failure' | 'partial' | 'blocked' | 'error';

export type AuditSource = 'user' | 'system' | 'api' | 'webhook' | 'scheduled' | 'automated';

export type SecurityEventType = 
  | 'login' | 'logout' | 'permission_change' | 'data_access' | 'configuration_change'
  | 'security_violation' | 'brute_force' | 'suspicious_activity' | 'unauthorized_access'
  | 'data_breach' | 'malware_detection' | 'phishing_attempt' | 'privilege_escalation'
  | 'account_takeover' | 'insider_threat' | 'compliance_violation';

export type SecuritySeverity = 'info' | 'low' | 'medium' | 'high' | 'critical';

export type ThreatLevel = 'minimal' | 'low' | 'moderate' | 'high' | 'severe';

export type Environment = 'production' | 'staging' | 'development' | 'testing' | 'sandbox';

export type SessionType = 'interactive' | 'api' | 'service' | 'scheduled' | 'system';

export type AuthenticationMethod = 
  | 'password' | 'mfa' | 'sso' | 'api_key' | 'oauth' | 'certificate' | 'biometric';

export type SecurityEventSource = 
  | 'waf' | 'ids' | 'antivirus' | 'firewall' | 'application' | 'user_report' | 'automated_scan';

export type RecommendationType = 
  | 'security_policy' | 'access_control' | 'monitoring' | 'training' | 'technical' | 'process';

export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical';

export type ConfidenceLevel = 'very_low' | 'low' | 'medium' | 'high' | 'very_high';

// Complex Supporting Interfaces
export interface TimeRange {
  start: string;
  end: string;
}

export interface FieldChange {
  field: string;
  old_value: any;
  new_value: any;
  change_type: ChangeType;
  sensitive: boolean;
}

export interface AuditError {
  code: string;
  message: string;
  details?: string;
  stack_trace?: string;
}

export interface DataVolume {
  records: number;
  size_bytes: number;
  affected_tables?: string[];
  query_complexity?: number;
}

export interface ImpactAssessment {
  users_affected: number;
  accounts_affected: number;
  data_sensitivity: DataSensitivity;
  business_impact: BusinessImpact;
  technical_impact: TechnicalImpact;
}

export interface ComplianceContext {
  frameworks: string[];
  requirements: string[];
  controls: string[];
  exceptions: ComplianceException[];
}

export interface GeoLocation {
  country: string;
  region: string;
  city: string;
  latitude?: number;
  longitude?: number;
  timezone: string;
  isp?: string;
  is_vpn?: boolean;
  is_tor?: boolean;
}

export interface DeviceInfo {
  type: DeviceType;
  os: string;
  browser?: string;
  mobile: boolean;
  fingerprint: string;
  trusted: boolean;
  first_seen: string;
  last_seen: string;
}

export interface AffectedResource {
  resource_type: string;
  resource_id: string;
  resource_name?: string;
  impact_level: ImpactLevel;
  compromise_indicators: string[];
}

export interface SecurityIndicator {
  type: IndicatorType;
  value: string;
  confidence: ConfidenceLevel;
  threat_intel_match: boolean;
  first_seen: string;
  last_seen: string;
  context: IndicatorContext;
}

export interface MitigationInfo {
  actions_taken: MitigationAction[];
  effectiveness: EffectivenessLevel;
  automated: boolean;
  manual_steps: string[];
  timeline: MitigationTimeline[];
}

export interface InvestigationInfo {
  status: InvestigationStatus;
  assigned_to?: string;
  started_at: string;
  findings: InvestigationFinding[];
  evidence_collected: Evidence[];
  next_steps: string[];
}

export interface SecurityEventMetadata {
  correlation_id: string;
  investigation_id?: string;
  incident_id?: string;
  source_system: string;
  detection_rule?: string;
  false_positive: boolean;
  analyst_notes?: string[];
  tags: string[];
}

export interface ThreatActor {
  type: ThreatActorType;
  sophistication: SophisticationLevel;
  motivation: Motivation[];
  attribution?: string;
  tactics: string[];
  techniques: string[];
  procedures: string[];
}

export interface CompromiseAssessment {
  likely_compromised: boolean;
  confidence: ConfidenceLevel;
  scope: CompromiseScope;
  persistence: PersistenceIndicator[];
  data_accessed: DataAccess[];
  lateral_movement: LateralMovement[];
}

export interface SecurityTimeline {
  timestamp: string;
  event: string;
  source: string;
  details: Record<string, any>;
}

export interface Evidence {
  type: EvidenceType;
  description: string;
  collected_at: string;
  hash?: string;
  size?: number;
  chain_of_custody: CustodyEntry[];
  analysis_results?: AnalysisResult[];
}

export interface SecurityImpact {
  confidentiality: ImpactLevel;
  integrity: ImpactLevel;
  availability: ImpactLevel;
  financial: FinancialImpact;
  reputational: ReputationalImpact;
  regulatory: RegulatoryImpact;
}

export interface RiskDistribution {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

export interface TrendInfo {
  direction: TrendDirection;
  rate: number;
  prediction: TrendPrediction;
}

export interface ActivityLocation {
  location: GeoLocation;
  count: number;
  first_seen: string;
  last_seen: string;
  risk_score: number;
}

export interface ActivityDevice {
  device: DeviceInfo;
  count: number;
  first_seen: string;
  last_seen: string;
  risk_score: number;
}

export interface ActivityPattern {
  pattern_type: PatternType;
  description: string;
  frequency: number;
  confidence: ConfidenceLevel;
  baseline_deviation: number;
}

export interface ActivityAnomaly {
  anomaly_type: AnomalyType;
  description: string;
  severity: AnomalySeverity;
  confidence: ConfidenceLevel;
  detected_at: string;
  investigated: boolean;
}

export interface IncidentTypeCount {
  type: SecurityEventType;
  count: number;
  trend: TrendDirection;
  average_severity: number;
}

export interface TrendingThreat {
  threat_type: string;
  count: number;
  growth_rate: number;
  impact_score: number;
  geographical_spread: number;
}

export interface FinancialImpact {
  estimated_cost: number;
  currency: string;
  cost_breakdown: CostBreakdown[];
  confidence: ConfidenceLevel;
}

export interface EffortEstimate {
  person_hours: number;
  complexity: ComplexityLevel;
  dependencies: number;
  timeline: string;
}

export interface RiskReduction {
  score_improvement: number;
  threats_mitigated: string[];
  vulnerabilities_addressed: string[];
  compliance_enhancement: string[];
}

export interface ComplianceImpact {
  frameworks_affected: string[];
  controls_strengthened: string[];
  audit_readiness_improvement: number;
  risk_profile_enhancement: string;
}

export interface RecommendationResource {
  type: ResourceType;
  name: string;
  url?: string;
  description: string;
}

// Additional enums and types
export type ChangeType = 'create' | 'update' | 'delete' | 'restore' | 'encrypt' | 'decrypt';
export type DataSensitivity = 'public' | 'internal' | 'confidential' | 'restricted';
export type BusinessImpact = 'none' | 'minimal' | 'moderate' | 'significant' | 'severe';
export type TechnicalImpact = 'none' | 'minimal' | 'moderate' | 'significant' | 'severe';
export type DeviceType = 'desktop' | 'mobile' | 'tablet' | 'server' | 'iot' | 'unknown';
export type ImpactLevel = 'none' | 'low' | 'medium' | 'high' | 'critical';
export type IndicatorType = 'ip' | 'domain' | 'url' | 'hash' | 'email' | 'user_agent' | 'certificate';
export type EffectivenessLevel = 'ineffective' | 'partially_effective' | 'effective' | 'highly_effective';
export type InvestigationStatus = 'open' | 'in_progress' | 'pending' | 'closed' | 'escalated';
export type ThreatActorType = 'nation_state' | 'cybercriminal' | 'hacktivist' | 'insider' | 'unknown';
export type SophisticationLevel = 'low' | 'medium' | 'high' | 'advanced';
export type EvidenceType = 'log' | 'network_capture' | 'file' | 'memory_dump' | 'screenshot' | 'metadata';
export type ReputationalImpact = 'none' | 'minimal' | 'moderate' | 'significant' | 'severe';
export type RegulatoryImpact = 'none' | 'minimal' | 'moderate' | 'significant' | 'severe';
export type TrendDirection = 'increasing' | 'decreasing' | 'stable' | 'volatile';
export type PatternType = 'temporal' | 'behavioral' | 'access' | 'network' | 'resource_usage';
export type AnomalyType = 'statistical' | 'behavioral' | 'temporal' | 'geographical' | 'access_pattern';
export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';
export type ComplexityLevel = 'simple' | 'moderate' | 'complex' | 'very_complex';
export type ResourceType = 'documentation' | 'tool' | 'service' | 'training' | 'template';

// Additional complex interfaces would be defined here for completeness...
export interface ComplianceException {
  exception_id: string;
  reason: string;
  approved_by: string;
  expires_at?: string;
}

export interface MitigationAction {
  action: string;
  timestamp: string;
  effectiveness: EffectivenessLevel;
  automated: boolean;
}

export interface MitigationTimeline {
  timestamp: string;
  action: string;
  result: string;
  automated: boolean;
}

export interface InvestigationFinding {
  finding: string;
  evidence_references: string[];
  confidence: ConfidenceLevel;
  impact: ImpactLevel;
}

export interface IndicatorContext {
  source: string;
  campaign?: string;
  family?: string;
  tags: string[];
}

export interface CompromiseScope {
  systems_affected: number;
  users_affected: number;
  data_types: string[];
  timeframe: TimeRange;
}

export interface PersistenceIndicator {
  mechanism: string;
  location: string;
  confidence: ConfidenceLevel;
}

export interface DataAccess {
  data_type: string;
  volume: DataVolume;
  sensitivity: DataSensitivity;
  timestamp: string;
}

export interface LateralMovement {
  source_system: string;
  target_system: string;
  method: string;
  timestamp: string;
  success: boolean;
}

export interface CustodyEntry {
  timestamp: string;
  handler: string;
  action: string;
  notes?: string;
}

export interface AnalysisResult {
  tool: string;
  result: string;
  confidence: ConfidenceLevel;
  timestamp: string;
}

export interface TrendPrediction {
  next_period: number;
  confidence: ConfidenceLevel;
  factors: string[];
}

export interface CostBreakdown {
  category: string;
  amount: number;
  description: string;
}

export type Motivation = 'financial' | 'espionage' | 'disruption' | 'ideology' | 'unknown';