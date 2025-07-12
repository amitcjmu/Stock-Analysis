/**
 * Assessment API Types
 * 
 * Type definitions for Assessment flow API endpoints, requests, and responses.
 * Covers application assessment, infrastructure analysis, and readiness evaluation.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ListRequest,
  ListResponse,
  GetRequest,
  GetResponse,
  CreateRequest,
  CreateResponse,
  UpdateRequest,
  UpdateResponse,
  DeleteRequest,
  DeleteResponse,
  ValidationResult,
  ExportRequest,
  ExportResponse
} from './shared';

// Assessment Flow Management APIs
export interface InitializeAssessmentFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  assessmentType: 'application' | 'infrastructure' | 'security' | 'data' | 'comprehensive';
  scope: AssessmentScope;
  parentFlowId?: string;
  configuration?: AssessmentFlowConfiguration;
  template?: string;
  metadata?: Record<string, any>;
}

export interface InitializeAssessmentFlowResponse extends BaseApiResponse<AssessmentFlowData> {
  data: AssessmentFlowData;
  flowId: string;
  initialState: AssessmentState;
  nextSteps: string[];
  assessmentPlan: AssessmentPlan;
  recommendations?: string[];
}

export interface GetAssessmentFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeAnalytics?: boolean;
  includeRecommendations?: boolean;
  includeRisks?: boolean;
  includeCompliance?: boolean;
}

export interface GetAssessmentFlowStatusResponse extends BaseApiResponse<AssessmentStatusDetail> {
  data: AssessmentStatusDetail;
  realTimeUpdates?: boolean;
  nextRefresh?: string;
  analytics?: AssessmentAnalytics;
}

export interface ListAssessmentFlowsRequest extends ListRequest {
  assessmentTypes?: string[];
  status?: AssessmentStatus[];
  priorities?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'completed' | 'started';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
  includeCompliance?: boolean;
}

export interface ListAssessmentFlowsResponse extends ListResponse<AssessmentFlowSummary> {
  data: AssessmentFlowSummary[];
  aggregations?: AssessmentAggregation[];
  trends?: AssessmentTrend[];
  compliance?: ComplianceSummary;
}

export interface UpdateAssessmentFlowRequest extends UpdateRequest<Partial<AssessmentFlowData>> {
  flowId: string;
  data: Partial<AssessmentFlowData>;
  validateTransition?: boolean;
  skipValidation?: boolean;
  updateRisks?: boolean;
  updateCompliance?: boolean;
}

export interface UpdateAssessmentFlowResponse extends UpdateResponse<AssessmentFlowData> {
  data: AssessmentFlowData;
  transitionResult?: AssessmentTransitionResult;
  riskUpdates?: RiskAssessmentUpdate[];
  complianceUpdates?: ComplianceUpdate[];
}

// Application Assessment APIs
export interface CreateApplicationAssessmentRequest extends CreateRequest<ApplicationAssessmentData> {
  flowId: string;
  data: ApplicationAssessmentData;
  analysisDepth: 'surface' | 'standard' | 'deep' | 'comprehensive';
  includeDependencies?: boolean;
  includePerformance?: boolean;
  includeSecurity?: boolean;
  includeCompliance?: boolean;
}

export interface CreateApplicationAssessmentResponse extends CreateResponse<ApplicationAssessmentResult> {
  data: ApplicationAssessmentResult;
  assessmentId: string;
  executionPlan: AssessmentExecutionPlan;
  estimatedDuration: number;
  requiredResources: AssessmentResource[];
}

export interface GetApplicationAssessmentRequest extends GetRequest {
  assessmentId: string;
  includeDetails?: boolean;
  includeFindings?: boolean;
  includeRecommendations?: boolean;
  includeComplexity?: boolean;
  includeRisks?: boolean;
}

export interface GetApplicationAssessmentResponse extends GetResponse<ApplicationAssessmentResult> {
  data: ApplicationAssessmentResult;
  findings: AssessmentFinding[];
  recommendations: AssessmentRecommendation[];
  complexityAnalysis: ComplexityAnalysis;
  riskProfile: RiskProfile;
}

export interface ListApplicationAssessmentsRequest extends ListRequest {
  flowId?: string;
  applicationTypes?: string[];
  technologies?: string[];
  complexityLevels?: string[];
  riskLevels?: string[];
  status?: AssessmentStatus[];
  dateRange?: {
    start: string;
    end: string;
  };
}

export interface ListApplicationAssessmentsResponse extends ListResponse<ApplicationAssessmentSummary> {
  data: ApplicationAssessmentSummary[];
  statistics: AssessmentStatistics;
  trends: AssessmentTrend[];
  insights: AssessmentInsight[];
}

// Infrastructure Assessment APIs
export interface CreateInfrastructureAssessmentRequest extends CreateRequest<InfrastructureAssessmentData> {
  flowId: string;
  data: InfrastructureAssessmentData;
  assessmentScope: InfrastructureScope;
  includeNetworking?: boolean;
  includeSecurity?: boolean;
  includePerformance?: boolean;
  includeCapacity?: boolean;
  includeCompliance?: boolean;
}

export interface CreateInfrastructureAssessmentResponse extends CreateResponse<InfrastructureAssessmentResult> {
  data: InfrastructureAssessmentResult;
  assessmentId: string;
  discoveredResources: InfrastructureResource[];
  assessmentPlan: InfrastructureAssessmentPlan;
}

export interface GetInfrastructureAssessmentRequest extends GetRequest {
  assessmentId: string;
  includeTopology?: boolean;
  includePerformance?: boolean;
  includeSecurity?: boolean;
  includeCapacity?: boolean;
  includeCosts?: boolean;
}

export interface GetInfrastructureAssessmentResponse extends GetResponse<InfrastructureAssessmentResult> {
  data: InfrastructureAssessmentResult;
  topology: InfrastructureTopology;
  performanceMetrics: PerformanceMetrics;
  securityAssessment: SecurityAssessment;
  capacityAnalysis: CapacityAnalysis;
  costAnalysis: CostAnalysis;
}

// Risk Assessment APIs
export interface CreateRiskAssessmentRequest extends CreateRequest<RiskAssessmentData> {
  flowId: string;
  data: RiskAssessmentData;
  riskCategories: string[];
  assessmentMethod: 'automated' | 'manual' | 'hybrid';
  includeQuantitative?: boolean;
  includeQualitative?: boolean;
  includeMitigation?: boolean;
}

export interface CreateRiskAssessmentResponse extends CreateResponse<RiskAssessmentResult> {
  data: RiskAssessmentResult;
  riskProfile: RiskProfile;
  mitigationPlan?: MitigationPlan;
  complianceGaps?: ComplianceGap[];
}

export interface GetRiskAssessmentRequest extends GetRequest {
  assessmentId: string;
  includeDetails?: boolean;
  includeQuantification?: boolean;
  includeMitigation?: boolean;
  includeCompliance?: boolean;
  includeTimeline?: boolean;
}

export interface GetRiskAssessmentResponse extends GetResponse<RiskAssessmentResult> {
  data: RiskAssessmentResult;
  riskMatrix: RiskMatrix;
  quantification: RiskQuantification;
  mitigationStrategies: MitigationStrategy[];
  complianceStatus: ComplianceStatus;
}

// Compliance Assessment APIs
export interface CreateComplianceAssessmentRequest extends CreateRequest<ComplianceAssessmentData> {
  flowId: string;
  data: ComplianceAssessmentData;
  frameworks: string[];
  standards: string[];
  regulations: string[];
  assessmentScope: ComplianceScope;
  includeGapAnalysis?: boolean;
  includeRemediation?: boolean;
}

export interface CreateComplianceAssessmentResponse extends CreateResponse<ComplianceAssessmentResult> {
  data: ComplianceAssessmentResult;
  complianceScore: number;
  gapAnalysis?: GapAnalysis;
  remediationPlan?: RemediationPlan;
  certificationReadiness?: CertificationReadiness;
}

export interface GetComplianceAssessmentRequest extends GetRequest {
  assessmentId: string;
  frameworks?: string[];
  includeDetails?: boolean;
  includeEvidence?: boolean;
  includeRemediation?: boolean;
  includeCertification?: boolean;
}

export interface GetComplianceAssessmentResponse extends GetResponse<ComplianceAssessmentResult> {
  data: ComplianceAssessmentResult;
  frameworkResults: FrameworkAssessmentResult[];
  evidence: ComplianceEvidence[];
  gaps: ComplianceGap[];
  recommendations: ComplianceRecommendation[];
}

// Readiness Assessment APIs
export interface CreateReadinessAssessmentRequest extends CreateRequest<ReadinessAssessmentData> {
  flowId: string;
  data: ReadinessAssessmentData;
  targetPlatform: string;
  migrationStrategy: string;
  assessmentCriteria: ReadinessCriteria[];
  includeSkillsGap?: boolean;
  includeResourcePlanning?: boolean;
  includeTimelineEstimation?: boolean;
}

export interface CreateReadinessAssessmentResponse extends CreateResponse<ReadinessAssessmentResult> {
  data: ReadinessAssessmentResult;
  readinessScore: number;
  readinessLevel: 'not_ready' | 'partially_ready' | 'ready' | 'highly_ready';
  blockers: ReadinessBlocker[];
  recommendations: ReadinessRecommendation[];
}

export interface GetReadinessAssessmentRequest extends GetRequest {
  assessmentId: string;
  includeSkillsAnalysis?: boolean;
  includeResourceAnalysis?: boolean;
  includeTimelineAnalysis?: boolean;
  includeRiskAnalysis?: boolean;
}

export interface GetReadinessAssessmentResponse extends GetResponse<ReadinessAssessmentResult> {
  data: ReadinessAssessmentResult;
  skillsGapAnalysis: SkillsGapAnalysis;
  resourceRequirements: ResourceRequirements;
  timelineEstimation: TimelineEstimation;
  readinessRoadmap: ReadinessRoadmap;
}

// Assessment Analytics and Reporting APIs
export interface GetAssessmentAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  assessmentIds?: string[];
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  context: MultiTenantContext;
}

export interface GetAssessmentAnalyticsResponse extends BaseApiResponse<AssessmentAnalytics> {
  data: AssessmentAnalytics;
  insights: AnalyticsInsight[];
  trends: AnalyticsTrend[];
  benchmarks: AnalyticsBenchmark[];
}

export interface GenerateAssessmentReportRequest extends BaseApiRequest {
  assessmentId: string;
  reportType: 'executive' | 'technical' | 'compliance' | 'comprehensive';
  format: 'pdf' | 'html' | 'docx' | 'json';
  sections?: string[];
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateAssessmentReportResponse extends BaseApiResponse<AssessmentReport> {
  data: AssessmentReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

export interface ExportAssessmentDataRequest extends ExportRequest {
  assessmentId: string;
  exportType: 'findings' | 'recommendations' | 'risks' | 'compliance' | 'all';
  includeMetadata?: boolean;
  includeAnalytics?: boolean;
}

export interface ExportAssessmentDataResponse extends ExportResponse {
  exportId: string;
  sections: string[];
  recordCount: number;
  estimatedSize: number;
}

// Assessment Execution APIs
export interface ExecuteAssessmentRequest extends BaseApiRequest {
  assessmentId: string;
  executionConfig?: AssessmentExecutionConfig;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
  scheduledTime?: string;
  notificationSettings?: NotificationSettings;
  context: MultiTenantContext;
}

export interface ExecuteAssessmentResponse extends BaseApiResponse<AssessmentExecution> {
  data: AssessmentExecution;
  executionId: string;
  estimatedDuration: number;
  trackingUrl: string;
}

export interface GetAssessmentExecutionStatusRequest extends GetRequest {
  executionId: string;
  includeProgress?: boolean;
  includeLogs?: boolean;
  includeMetrics?: boolean;
}

export interface GetAssessmentExecutionStatusResponse extends GetResponse<AssessmentExecutionStatus> {
  data: AssessmentExecutionStatus;
  progress: ExecutionProgress;
  logs: ExecutionLog[];
  metrics: ExecutionMetrics;
}

// Supporting Data Types
export interface AssessmentFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  assessmentType: string;
  status: AssessmentStatus;
  priority: 'low' | 'medium' | 'high' | 'critical';
  scope: AssessmentScope;
  progress: number;
  phases: AssessmentPhases;
  currentPhase: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  metadata: Record<string, any>;
}

export interface AssessmentScope {
  applications: string[];
  infrastructure: string[];
  data: string[];
  security: string[];
  compliance: string[];
  geography: string[];
  businessUnits: string[];
  timeframe: {
    start: string;
    end: string;
  };
  exclusions?: string[];
  constraints?: string[];
}

export interface AssessmentFlowConfiguration {
  automated: boolean;
  parallelExecution: boolean;
  continuousAssessment: boolean;
  riskTolerance: 'low' | 'medium' | 'high';
  complianceRequired: boolean;
  reportingFrequency: string;
  notificationSettings: NotificationSettings;
  integrations: IntegrationConfig[];
  customRules: CustomRule[];
}

export interface AssessmentState {
  flowId: string;
  currentPhase: string;
  nextPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseResults: Record<string, any>;
  assessmentResults: Record<string, any>;
  riskProfile: RiskProfile;
  complianceStatus: ComplianceStatus;
  blockers: AssessmentBlocker[];
  warnings: AssessmentWarning[];
  recommendations: AssessmentRecommendation[];
  createdAt: string;
  updatedAt: string;
}

export interface AssessmentPlan {
  phases: AssessmentPhaseDefinition[];
  timeline: AssessmentTimeline;
  resources: AssessmentResource[];
  dependencies: AssessmentDependency[];
  riskMitigation: RiskMitigationPlan[];
  qualityGates: QualityGate[];
  deliverables: AssessmentDeliverable[];
}

export interface AssessmentStatusDetail {
  flowId: string;
  status: AssessmentStatus;
  progress: number;
  currentPhase: string;
  phaseDetails: PhaseDetail[];
  findings: AssessmentFinding[];
  risks: Risk[];
  recommendations: AssessmentRecommendation[];
  compliance: ComplianceStatus;
  blockers: AssessmentBlocker[];
  nextActions: NextAction[];
  lastUpdated: string;
}

export interface AssessmentAnalytics {
  summary: AssessmentSummary;
  trends: AssessmentTrend[];
  benchmarks: AssessmentBenchmark[];
  insights: AssessmentInsight[];
  predictions: AssessmentPrediction[];
  correlations: AssessmentCorrelation[];
  outliers: AssessmentOutlier[];
}

export interface AssessmentFlowSummary {
  id: string;
  flowId: string;
  flowName: string;
  assessmentType: string;
  status: AssessmentStatus;
  progress: number;
  priority: string;
  riskLevel: string;
  complianceScore: number;
  findingsCount: number;
  blockerCount: number;
  createdAt: string;
  updatedAt: string;
  estimatedCompletion?: string;
}

export interface ApplicationAssessmentData {
  applicationId: string;
  applicationName: string;
  applicationDescription?: string;
  applicationType: string;
  technology: Technology[];
  architecture: ApplicationArchitecture;
  dependencies: ApplicationDependency[];
  integrations: ApplicationIntegration[];
  dataAssets: DataAsset[];
  securityConfig: SecurityConfiguration;
  performanceProfile: PerformanceProfile;
  currentEnvironment: EnvironmentConfiguration;
  businessCriticality: 'low' | 'medium' | 'high' | 'critical';
  complianceRequirements: string[];
  customAttributes: Record<string, any>;
}

export interface ApplicationAssessmentResult {
  assessmentId: string;
  applicationId: string;
  status: AssessmentStatus;
  overallScore: number;
  complexity: ComplexityScore;
  modernizationReadiness: ReadinessScore;
  riskProfile: RiskProfile;
  migrationEffort: EffortEstimation;
  recommendations: AssessmentRecommendation[];
  findings: AssessmentFinding[];
  technicalDebt: TechnicalDebtAnalysis;
  architecturalFitness: ArchitecturalFitness;
  securityPosture: SecurityPosture;
  performanceProfile: PerformanceProfile;
  complianceAlignment: ComplianceAlignment;
  businessImpact: BusinessImpactAnalysis;
  assessedAt: string;
  assessedBy: string;
  metadata: Record<string, any>;
}

export interface InfrastructureAssessmentData {
  infrastructureId: string;
  name: string;
  description?: string;
  scope: InfrastructureScope;
  components: InfrastructureComponent[];
  networks: NetworkConfiguration[];
  security: SecurityConfiguration;
  monitoring: MonitoringConfiguration;
  backup: BackupConfiguration;
  disaster_recovery: DisasterRecoveryConfiguration;
  compliance: ComplianceConfiguration;
  cost_profile: CostProfile;
  current_utilization: UtilizationMetrics;
  performance_baseline: PerformanceBaseline;
  capacity_planning: CapacityPlanningData;
  customAttributes: Record<string, any>;
}

export interface InfrastructureAssessmentResult {
  assessmentId: string;
  infrastructureId: string;
  status: AssessmentStatus;
  overallScore: number;
  readinessLevel: ReadinessLevel;
  migrationComplexity: ComplexityScore;
  riskProfile: RiskProfile;
  costOptimizationPotential: number;
  securityPosture: SecurityPosture;
  complianceStatus: ComplianceStatus;
  performanceAnalysis: PerformanceAnalysis;
  capacityAnalysis: CapacityAnalysis;
  networkAssessment: NetworkAssessment;
  findings: AssessmentFinding[];
  recommendations: AssessmentRecommendation[];
  migrationPlan: MigrationPlan;
  assessedAt: string;
  assessedBy: string;
}

export type AssessmentStatus = 
  | 'pending' | 'in_progress' | 'paused' | 'completed' 
  | 'failed' | 'cancelled' | 'waiting_for_input' | 'under_review';

export type ReadinessLevel = 
  | 'not_ready' | 'partially_ready' | 'ready' | 'highly_ready' | 'optimal';

export type ComplexityLevel = 
  | 'very_low' | 'low' | 'medium' | 'high' | 'very_high' | 'extreme';

export type RiskLevel = 
  | 'very_low' | 'low' | 'medium' | 'high' | 'very_high' | 'critical';

// Additional supporting interfaces would continue here...
// (Truncated for brevity, but would include all the referenced types like
// AssessmentFinding, AssessmentRecommendation, RiskProfile, etc.)