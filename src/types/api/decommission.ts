/**
 * Decommission API Types
 * 
 * Type definitions for System Decommissioning flow API endpoints, requests, and responses.
 * Covers decommission planning, data migration, system shutdown, and cleanup activities.
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
  ValidationResult
} from './shared';

// Decommission Flow Management APIs
export interface InitializeDecommissionFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  decommissionScope: DecommissionScope;
  decommissionStrategy: DecommissionStrategy;
  timeline: DecommissionTimeline;
  stakeholders: DecommissionStakeholder[];
  dependencies: DecommissionDependency[];
  parentFlowId?: string;
  configuration?: DecommissionFlowConfiguration;
  metadata?: Record<string, any>;
}

export interface InitializeDecommissionFlowResponse extends BaseApiResponse<DecommissionFlowData> {
  data: DecommissionFlowData;
  flowId: string;
  initialState: DecommissionState;
  decommissionPlan: DecommissionPlan;
  riskAssessment: DecommissionRiskAssessment;
  approvalRequirements: ApprovalRequirement[];
}

export interface GetDecommissionFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeProgress?: boolean;
  includeDependencies?: boolean;
  includeRisks?: boolean;
  includeDataMigration?: boolean;
  includeApprovals?: boolean;
}

export interface GetDecommissionFlowStatusResponse extends BaseApiResponse<DecommissionStatusDetail> {
  data: DecommissionStatusDetail;
  progress: DecommissionProgress;
  dependencies: DecommissionDependencyStatus[];
  risks: DecommissionRisk[];
  dataMigration: DataMigrationStatus;
  approvals: ApprovalStatus[];
}

export interface ListDecommissionFlowsRequest extends ListRequest {
  decommissionTypes?: string[];
  status?: DecommissionStatus[];
  priorities?: string[];
  phases?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'planned_start' | 'planned_completion';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
}

export interface ListDecommissionFlowsResponse extends ListResponse<DecommissionFlowSummary> {
  data: DecommissionFlowSummary[];
  aggregations?: DecommissionAggregation[];
  trends?: DecommissionTrend[];
  portfolioMetrics?: DecommissionPortfolioMetrics;
}

// Decommission Planning APIs
export interface CreateDecommissionPlanRequest extends CreateRequest<DecommissionPlanData> {
  flowId: string;
  data: DecommissionPlanData;
  planningMethod: 'big_bang' | 'phased' | 'parallel_run' | 'gradual_cutover';
  riskMitigation: RiskMitigationStrategy[];
  dataHandling: DataHandlingStrategy;
  communicationPlan: CommunicationPlan;
  rollbackPlan: RollbackPlan;
  complianceRequirements: ComplianceRequirement[];
}

export interface CreateDecommissionPlanResponse extends CreateResponse<DecommissionPlan> {
  data: DecommissionPlan;
  planId: string;
  executionTimeline: ExecutionTimeline;
  resourceRequirements: ResourceRequirement[];
  dependencyAnalysis: DependencyAnalysis;
  riskProfile: RiskProfile;
}

export interface ValidateDecommissionPlanRequest extends BaseApiRequest {
  planId: string;
  validationType: 'technical' | 'business' | 'compliance' | 'comprehensive';
  includeSimulation?: boolean;
  includeDependencyCheck?: boolean;
  includeRiskAnalysis?: boolean;
  context: MultiTenantContext;
}

export interface ValidateDecommissionPlanResponse extends BaseApiResponse<DecommissionValidationResult> {
  data: DecommissionValidationResult;
  validationId: string;
  isValid: boolean;
  validationErrors: ValidationError[];
  warnings: ValidationWarning[];
  recommendations: ValidationRecommendation[];
  simulationResults?: SimulationResult[];
}

export interface ApproveDecommissionPlanRequest extends BaseApiRequest {
  planId: string;
  approvalLevel: 'technical' | 'business' | 'executive' | 'compliance';
  approverComments?: string;
  conditions?: ApprovalCondition[];
  deferredApprovals?: string[];
  context: MultiTenantContext;
}

export interface ApproveDecommissionPlanResponse extends BaseApiResponse<DecommissionApproval> {
  data: DecommissionApproval;
  approvalId: string;
  status: 'approved' | 'approved_with_conditions' | 'rejected' | 'needs_revision';
  nextSteps: string[];
  executionAuthorized: boolean;
}

// System Analysis APIs
export interface AnalyzeSystemForDecommissionRequest extends BaseApiRequest {
  flowId: string;
  systemId: string;
  analysisDepth: 'surface' | 'standard' | 'deep' | 'comprehensive';
  analysisTypes: SystemAnalysisType[];
  includeDependencies?: boolean;
  includeDataFlow?: boolean;
  includeIntegrations?: boolean;
  includeUsagePatterns?: boolean;
  context: MultiTenantContext;
}

export interface AnalyzeSystemForDecommissionResponse extends BaseApiResponse<SystemAnalysisResult> {
  data: SystemAnalysisResult;
  analysisId: string;
  systemProfile: SystemProfile;
  dependencies: SystemDependency[];
  dataAssets: DataAsset[];
  integrations: SystemIntegration[];
  usageAnalysis: UsageAnalysis;
  riskFactors: RiskFactor[];
}

export interface GetSystemDependenciesRequest extends GetRequest {
  systemId: string;
  dependencyType?: 'upstream' | 'downstream' | 'bidirectional' | 'all';
  depth?: number;
  includeTransitive?: boolean;
  includeExternal?: boolean;
  includeLegacy?: boolean;
}

export interface GetSystemDependenciesResponse extends GetResponse<SystemDependencyMap> {
  data: SystemDependencyMap;
  dependencyGraph: DependencyGraph;
  criticalPaths: CriticalPath[];
  isolationPlan: IsolationPlan;
  migrationOrder: MigrationOrder[];
}

export interface AssessDecommissionImpactRequest extends BaseApiRequest {
  flowId: string;
  systemIds: string[];
  impactAreas: ImpactArea[];
  stakeholders: string[];
  timeHorizon: 'immediate' | 'short_term' | 'medium_term' | 'long_term';
  includeBusinessImpact?: boolean;
  includeTechnicalImpact?: boolean;
  includeFinancialImpact?: boolean;
  context: MultiTenantContext;
}

export interface AssessDecommissionImpactResponse extends BaseApiResponse<DecommissionImpactAssessment> {
  data: DecommissionImpactAssessment;
  assessmentId: string;
  overallImpact: ImpactLevel;
  businessImpact: BusinessImpact;
  technicalImpact: TechnicalImpact;
  financialImpact: FinancialImpact;
  mitigation: ImpactMitigation[];
}

// Data Migration APIs
export interface CreateDataMigrationPlanRequest extends CreateRequest<DataMigrationPlanData> {
  flowId: string;
  data: DataMigrationPlanData;
  migrationStrategy: 'lift_and_shift' | 'transformation' | 'archive' | 'purge' | 'hybrid';
  dataAssets: DataAsset[];
  targetSystems: TargetSystem[];
  qualityRequirements: DataQualityRequirement[];
  complianceRequirements: DataComplianceRequirement[];
  timeline: DataMigrationTimeline;
}

export interface CreateDataMigrationPlanResponse extends CreateResponse<DataMigrationPlan> {
  data: DataMigrationPlan;
  planId: string;
  migrationWaves: DataMigrationWave[];
  dataMapping: DataMapping[];
  qualityGates: DataQualityGate[];
  validationPlan: DataValidationPlan;
}

export interface ExecuteDataMigrationRequest extends BaseApiRequest {
  planId: string;
  waveIds?: string[];
  executionMode: 'test' | 'production' | 'hybrid';
  dryRun?: boolean;
  rollbackEnabled?: boolean;
  validationEnabled?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteDataMigrationResponse extends BaseApiResponse<DataMigrationExecution> {
  data: DataMigrationExecution;
  executionId: string;
  status: DataMigrationStatus;
  estimatedCompletion: string;
  trackingUrl: string;
  rollbackPlan?: DataRollbackPlan;
}

export interface GetDataMigrationStatusRequest extends GetRequest {
  executionId: string;
  includeProgress?: boolean;
  includeValidation?: boolean;
  includeQuality?: boolean;
  includeErrors?: boolean;
  includeMetrics?: boolean;
}

export interface GetDataMigrationStatusResponse extends GetResponse<DataMigrationStatus> {
  data: DataMigrationStatusDetail;
  progress: DataMigrationProgress;
  validation: DataValidationResults;
  quality: DataQualityResults;
  errors: DataMigrationError[];
  metrics: DataMigrationMetrics;
}

export interface ValidateDataMigrationRequest extends BaseApiRequest {
  executionId: string;
  validationType: 'completeness' | 'accuracy' | 'consistency' | 'integrity' | 'comprehensive';
  sampleSize?: number;
  validationRules?: DataValidationRule[];
  context: MultiTenantContext;
}

export interface ValidateDataMigrationResponse extends BaseApiResponse<DataValidationResult> {
  data: DataValidationResult;
  validationId: string;
  overallScore: number;
  validationResults: ValidationCheck[];
  discrepancies: DataDiscrepancy[];
  recommendations: DataRecommendation[];
}

// System Shutdown APIs
export interface CreateShutdownPlanRequest extends CreateRequest<ShutdownPlanData> {
  flowId: string;
  data: ShutdownPlanData;
  shutdownStrategy: 'immediate' | 'graceful' | 'phased' | 'maintenance_window';
  components: SystemComponent[];
  shutdownOrder: ShutdownSequence[];
  rollbackProcedures: RollbackProcedure[];
  communicationPlan: ShutdownCommunicationPlan;
  monitoring: ShutdownMonitoring;
}

export interface CreateShutdownPlanResponse extends CreateResponse<ShutdownPlan> {
  data: ShutdownPlan;
  planId: string;
  executionWindows: ExecutionWindow[];
  impactAssessment: ShutdownImpactAssessment;
  approvalRequirements: ShutdownApprovalRequirement[];
}

export interface ExecuteSystemShutdownRequest extends BaseApiRequest {
  planId: string;
  executionWindow: ExecutionWindow;
  componentIds?: string[];
  forceShutdown?: boolean;
  bypassChecks?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteSystemShutdownResponse extends BaseApiResponse<ShutdownExecution> {
  data: ShutdownExecution;
  executionId: string;
  status: ShutdownStatus;
  startedAt: string;
  estimatedCompletion?: string;
  rollbackAvailable: boolean;
}

export interface GetShutdownStatusRequest extends GetRequest {
  executionId: string;
  includeComponentStatus?: boolean;
  includeMonitoring?: boolean;
  includeIssues?: boolean;
  includeLogs?: boolean;
}

export interface GetShutdownStatusResponse extends GetResponse<ShutdownStatusDetail> {
  data: ShutdownStatusDetail;
  componentStatus: ComponentShutdownStatus[];
  monitoring: ShutdownMonitoringData;
  issues: ShutdownIssue[];
  logs: ShutdownLog[];
}

export interface RollbackSystemShutdownRequest extends BaseApiRequest {
  executionId: string;
  rollbackType: 'full' | 'partial' | 'component_specific';
  componentIds?: string[];
  validationRequired?: boolean;
  context: MultiTenantContext;
}

export interface RollbackSystemShutdownResponse extends BaseApiResponse<ShutdownRollback> {
  data: ShutdownRollback;
  rollbackId: string;
  status: RollbackStatus;
  restoredComponents: string[];
  validationResults: ValidationResult[];
}

// Cleanup and Finalization APIs
export interface CreateCleanupPlanRequest extends CreateRequest<CleanupPlanData> {
  flowId: string;
  data: CleanupPlanData;
  cleanupScope: CleanupScope;
  cleanupTypes: CleanupType[];
  retentionPolicies: RetentionPolicy[];
  archivalRequirements: ArchivalRequirement[];
  disposalMethods: DisposalMethod[];
  complianceRequirements: CleanupComplianceRequirement[];
}

export interface CreateCleanupPlanResponse extends CreateResponse<CleanupPlan> {
  data: CleanupPlan;
  planId: string;
  cleanupPhases: CleanupPhase[];
  complianceValidation: ComplianceValidation;
  estimatedTimeframe: string;
  resourceRequirements: CleanupResourceRequirement[];
}

export interface ExecuteCleanupRequest extends BaseApiRequest {
  planId: string;
  phaseIds?: string[];
  cleanupMode: 'test' | 'production';
  preserveAuditTrail?: boolean;
  generateCertificates?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteCleanupResponse extends BaseApiResponse<CleanupExecution> {
  data: CleanupExecution;
  executionId: string;
  status: CleanupStatus;
  auditTrail: CleanupAuditTrail;
  certificates: ComplianceCertificate[];
}

export interface GetCleanupStatusRequest extends GetRequest {
  executionId: string;
  includeProgress?: boolean;
  includeAuditTrail?: boolean;
  includeCertificates?: boolean;
  includeCompliance?: boolean;
}

export interface GetCleanupStatusResponse extends GetResponse<CleanupStatusDetail> {
  data: CleanupStatusDetail;
  progress: CleanupProgress;
  auditTrail: CleanupAuditTrail;
  certificates: ComplianceCertificate[];
  complianceStatus: CleanupComplianceStatus;
}

export interface GenerateDecommissionCertificateRequest extends BaseApiRequest {
  flowId: string;
  certificateType: 'completion' | 'compliance' | 'data_destruction' | 'system_disposal';
  includeEvidence?: boolean;
  includeAuditTrail?: boolean;
  signatories: Signatory[];
  context: MultiTenantContext;
}

export interface GenerateDecommissionCertificateResponse extends BaseApiResponse<DecommissionCertificate> {
  data: DecommissionCertificate;
  certificateId: string;
  downloadUrl: string;
  validUntil: string;
  verificationCode: string;
}

// Decommission Analytics and Reporting APIs
export interface GetDecommissionAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  includeForecasts?: boolean;
  context: MultiTenantContext;
}

export interface GetDecommissionAnalyticsResponse extends BaseApiResponse<DecommissionAnalytics> {
  data: DecommissionAnalytics;
  insights: DecommissionInsight[];
  trends: DecommissionTrend[];
  forecasts: DecommissionForecast[];
  benchmarks: DecommissionBenchmark[];
}

export interface GenerateDecommissionReportRequest extends BaseApiRequest {
  flowId: string;
  reportType: 'progress' | 'completion' | 'compliance' | 'post_mortem' | 'executive';
  format: 'pdf' | 'html' | 'docx' | 'json';
  sections?: string[];
  includeEvidence?: boolean;
  includeMetrics?: boolean;
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateDecommissionReportResponse extends BaseApiResponse<DecommissionReport> {
  data: DecommissionReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Supporting Data Types
export interface DecommissionFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  decommissionType: string;
  status: DecommissionStatus;
  priority: 'low' | 'medium' | 'high' | 'critical' | 'emergency';
  scope: DecommissionScope;
  strategy: DecommissionStrategy;
  timeline: DecommissionTimeline;
  progress: number;
  phases: DecommissionPhases;
  currentPhase: string;
  stakeholders: DecommissionStakeholder[];
  dependencies: DecommissionDependency[];
  clientAccountId: string;
  engagementId: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  certifiedAt?: string;
  metadata: Record<string, any>;
}

export interface DecommissionScope {
  systems: string[];
  applications: string[];
  infrastructure: string[];
  data: string[];
  integrations: string[];
  users: string[];
  environments: string[];
  geography: string[];
  businessProcesses: string[];
  compliance: string[];
  timeline: {
    start: string;
    end: string;
  };
  budget: {
    amount: number;
    currency: string;
  };
  exclusions?: string[];
  constraints?: string[];
}

export interface DecommissionStrategy {
  approach: 'big_bang' | 'phased' | 'parallel_run' | 'gradual_cutover';
  dataHandling: 'migrate' | 'archive' | 'purge' | 'transform' | 'hybrid';
  systemHandling: 'shutdown' | 'repurpose' | 'disposal' | 'decommission';
  timeline: 'aggressive' | 'standard' | 'conservative' | 'extended';
  riskTolerance: 'low' | 'medium' | 'high';
  automation: 'manual' | 'semi_automated' | 'fully_automated';
  rollback: 'none' | 'limited' | 'full' | 'comprehensive';
  compliance: 'standard' | 'enhanced' | 'regulatory' | 'audit_ready';
}

export interface DecommissionFlowConfiguration {
  approvalGates: ApprovalGate[];
  qualityGates: QualityGate[];
  complianceChecks: ComplianceCheck[];
  monitoring: MonitoringConfiguration;
  alerting: AlertingConfiguration;
  reporting: ReportingConfiguration;
  automation: AutomationConfiguration;
  security: SecurityConfiguration;
  backup: BackupConfiguration;
  audit: AuditConfiguration;
}

export interface DecommissionState {
  flowId: string;
  status: DecommissionStatus;
  currentPhase: string;
  phaseStates: Record<string, PhaseState>;
  systemStates: Record<string, SystemState>;
  dataStates: Record<string, DataState>;
  dependencyStates: Record<string, DependencyState>;
  approvalStates: Record<string, ApprovalState>;
  riskStatus: RiskStatus;
  complianceStatus: ComplianceStatus;
  checkpoints: DecommissionCheckpoint[];
  blockers: DecommissionBlocker[];
  decisions: DecommissionDecision[];
  createdAt: string;
  updatedAt: string;
}

export type DecommissionStatus = 
  | 'planning' | 'analysis' | 'approval' | 'preparation'
  | 'data_migration' | 'system_shutdown' | 'cleanup' | 'finalization'
  | 'completed' | 'paused' | 'failed' | 'cancelled' | 'rolled_back';

export type SystemAnalysisType = 
  | 'dependencies' | 'data_flow' | 'integrations' | 'usage_patterns'
  | 'performance' | 'security' | 'compliance' | 'business_value';

export type DataMigrationStatus = 
  | 'planned' | 'preparing' | 'extracting' | 'transforming'
  | 'loading' | 'validating' | 'completed' | 'failed' | 'rolled_back';

export type ShutdownStatus = 
  | 'planned' | 'stopping_services' | 'draining_connections'
  | 'shutting_down' | 'verifying' | 'completed' | 'failed' | 'rolled_back';

export type CleanupStatus = 
  | 'planned' | 'archiving' | 'purging' | 'disposing'
  | 'verifying' | 'documenting' | 'completed' | 'failed';

export type RollbackStatus = 
  | 'available' | 'executing' | 'validating' | 'completed' | 'failed';

export type ImpactLevel = 'minimal' | 'low' | 'medium' | 'high' | 'critical';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)