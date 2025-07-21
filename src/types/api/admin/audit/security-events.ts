/**
 * Security Event Types
 * 
 * Security event logging and incident management types.
 * 
 * Generated with CC for modular admin type organization.
 */

import { 
  SecurityEventMetadata,
  ConfidenceLevel,
  ImpactLevel,
  Priority,
  EffortLevel,
  ReputationalImpact,
  RegulatoryImpact,
  TrendDirection
} from '../common';
import { 
  SecurityEventType, 
  SecuritySeverity,
  SecurityEventSource,
  ThreatLevel,
  IndicatorType,
  EffectivenessLevel,
  InvestigationStatus,
  ThreatActorType,
  SophisticationLevel,
  EvidenceType,
  RecommendationType,
  RecommendationPriority
} from './enums';

// Security event structure
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

// Security event details
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

// Affected resource
export interface AffectedResource {
  resource_type: string;
  resource_id: string;
  resource_name?: string;
  impact_level: ImpactLevel;
  compromise_indicators: string[];
}

// Security indicator
export interface SecurityIndicator {
  type: IndicatorType;
  value: string;
  confidence: ConfidenceLevel;
  threat_intel_match: boolean;
  first_seen: string;
  last_seen: string;
  context: IndicatorContext;
}

// Mitigation information
export interface MitigationInfo {
  actions_taken: MitigationAction[];
  effectiveness: EffectivenessLevel;
  automated: boolean;
  manual_steps: string[];
  timeline: MitigationTimeline[];
}

// Investigation information
export interface InvestigationInfo {
  status: InvestigationStatus;
  assigned_to?: string;
  started_at: string;
  findings: InvestigationFinding[];
  evidence_collected: Evidence[];
  next_steps: string[];
}

// Threat actor
export interface ThreatActor {
  type: ThreatActorType;
  sophistication: SophisticationLevel;
  motivation: Motivation[];
  attribution?: string;
  tactics: string[];
  techniques: string[];
  procedures: string[];
}

// Compromise assessment
export interface CompromiseAssessment {
  likely_compromised: boolean;
  confidence: ConfidenceLevel;
  scope: CompromiseScope;
  persistence: PersistenceIndicator[];
  data_accessed: DataAccess[];
  lateral_movement: LateralMovement[];
}

// Security timeline entry
export interface SecurityTimeline {
  timestamp: string;
  event: string;
  source: string;
  details: Record<string, any>;
}

// Evidence
export interface Evidence {
  type: EvidenceType;
  description: string;
  collected_at: string;
  hash?: string;
  size?: number;
  chain_of_custody: CustodyEntry[];
  analysis_results?: AnalysisResult[];
}

// Security impact
export interface SecurityImpact {
  confidentiality: ImpactLevel;
  integrity: ImpactLevel;
  availability: ImpactLevel;
  financial: FinancialImpact;
  reputational: ReputationalImpact;
  regulatory: RegulatoryImpact;
}

// Incident summary
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

// Security recommendation
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

// Supporting interfaces
export interface IndicatorContext {
  source: string;
  campaign?: string;
  family?: string;
  tags: string[];
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

export interface CostBreakdown {
  category: string;
  amount: number;
  description: string;
}

// Import common types
type TimeRange = import('../common').TimeRange;
type DataVolume = import('./audit-log').DataVolume;
type DataSensitivity = import('../common').DataSensitivity;
type ComplexityLevel = import('../common').ComplexityLevel;
type ResourceType = import('../common').ResourceType;

// Enums
export type Motivation = 'financial' | 'espionage' | 'disruption' | 'ideology' | 'unknown';