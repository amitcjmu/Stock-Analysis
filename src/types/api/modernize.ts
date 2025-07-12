/**
 * Modernize API Types
 * 
 * Type definitions for Application Modernization flow API endpoints, requests, and responses.
 * Covers code modernization, architecture transformation, and technology upgrades.
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

// Modernization Flow Management APIs
export interface InitializeModernizationFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  modernizationScope: ModernizationScope;
  targetArchitecture: TargetArchitecture;
  modernizationStrategy: ModernizationStrategy;
  constraints: ModernizationConstraint[];
  objectives: ModernizationObjective[];
  parentFlowId?: string;
  configuration?: ModernizationFlowConfiguration;
  metadata?: Record<string, any>;
}

export interface InitializeModernizationFlowResponse extends BaseApiResponse<ModernizationFlowData> {
  data: ModernizationFlowData;
  flowId: string;
  initialState: ModernizationState;
  modernizationPlan: ModernizationPlan;
  recommendations: ModernizationRecommendation[];
  riskAssessment: ModernizationRiskAssessment;
}

export interface GetModernizationFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeProgress?: boolean;
  includeAnalysis?: boolean;
  includeRecommendations?: boolean;
  includeRisks?: boolean;
  includeCodeMetrics?: boolean;
}

export interface GetModernizationFlowStatusResponse extends BaseApiResponse<ModernizationStatusDetail> {
  data: ModernizationStatusDetail;
  progress: ModernizationProgress;
  analysis: ModernizationAnalysis;
  codeMetrics: CodeMetrics;
  qualityAssessment: QualityAssessment;
}

export interface ListModernizationFlowsRequest extends ListRequest {
  modernizationTypes?: string[];
  status?: ModernizationStatus[];
  technologies?: string[];
  complexityLevels?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'started' | 'completed';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
}

export interface ListModernizationFlowsResponse extends ListResponse<ModernizationFlowSummary> {
  data: ModernizationFlowSummary[];
  aggregations?: ModernizationAggregation[];
  trends?: ModernizationTrend[];
  benchmarks?: ModernizationBenchmark[];
}

// Code Analysis APIs
export interface AnalyzeCodebaseRequest extends CreateRequest<CodebaseAnalysisData> {
  flowId: string;
  data: CodebaseAnalysisData;
  analysisDepth: 'surface' | 'standard' | 'deep' | 'comprehensive';
  analysisTypes: CodeAnalysisType[];
  includeMetrics?: boolean;
  includeDependencies?: boolean;
  includeSecurityScan?: boolean;
  includeQualityGates?: boolean;
}

export interface AnalyzeCodebaseResponse extends CreateResponse<CodeAnalysisResult> {
  data: CodeAnalysisResult;
  analysisId: string;
  executionPlan: AnalysisExecutionPlan;
  estimatedDuration: number;
  qualityScore: number;
}

export interface GetCodeAnalysisRequest extends GetRequest {
  analysisId: string;
  includeDetails?: boolean;
  includeMetrics?: boolean;
  includeFindings?: boolean;
  includeRecommendations?: boolean;
  includeDependencies?: boolean;
  includeSecurityFindings?: boolean;
}

export interface GetCodeAnalysisResponse extends GetResponse<CodeAnalysisResult> {
  data: CodeAnalysisResult;
  metrics: CodeMetrics;
  findings: CodeFinding[];
  recommendations: CodeRecommendation[];
  dependencies: DependencyAnalysis;
  securityFindings: SecurityFinding[];
}

export interface GenerateModernizationPlanRequest extends BaseApiRequest {
  flowId: string;
  analysisId: string;
  strategy: ModernizationStrategy;
  targetTechnology: TargetTechnology;
  constraints: ModernizationConstraint[];
  priorities: ModernizationPriority[];
  includeTimeline?: boolean;
  includeResourceEstimation?: boolean;
  includeRiskAssessment?: boolean;
  context: MultiTenantContext;
}

export interface GenerateModernizationPlanResponse extends BaseApiResponse<ModernizationPlan> {
  data: ModernizationPlan;
  planId: string;
  timeline: ModernizationTimeline;
  resourceEstimation: ResourceEstimation;
  riskAssessment: ModernizationRiskAssessment;
  alternatives: ModernizationAlternative[];
}

// Code Transformation APIs
export interface CreateTransformationJobRequest extends CreateRequest<TransformationJobData> {
  flowId: string;
  planId: string;
  data: TransformationJobData;
  transformationType: TransformationType;
  sourceLanguage: string;
  targetLanguage: string;
  transformationRules: TransformationRule[];
  validationRules: ValidationRule[];
  qualityGates: QualityGate[];
}

export interface CreateTransformationJobResponse extends CreateResponse<TransformationJob> {
  data: TransformationJob;
  jobId: string;
  estimatedDuration: number;
  transformationPlan: TransformationPlan;
  qualityAssurance: QualityAssurancePlan;
}

export interface GetTransformationJobStatusRequest extends GetRequest {
  jobId: string;
  includeProgress?: boolean;
  includeLogs?: boolean;
  includeMetrics?: boolean;
  includeOutput?: boolean;
  includeQualityResults?: boolean;
}

export interface GetTransformationJobStatusResponse extends GetResponse<TransformationJobStatus> {
  data: TransformationJobStatus;
  progress: TransformationProgress;
  logs: TransformationLog[];
  metrics: TransformationMetrics;
  output: TransformationOutput;
  qualityResults: QualityResults;
}

export interface ExecuteTransformationRequest extends BaseApiRequest {
  jobId: string;
  executionMode: 'validate' | 'transform' | 'full';
  dryRun?: boolean;
  parallelism?: number;
  checkpointingEnabled?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteTransformationResponse extends BaseApiResponse<TransformationExecution> {
  data: TransformationExecution;
  executionId: string;
  status: TransformationStatus;
  startedAt: string;
  trackingUrl: string;
}

// Refactoring APIs
export interface CreateRefactoringPlanRequest extends CreateRequest<RefactoringPlanData> {
  flowId: string;
  analysisId: string;
  data: RefactoringPlanData;
  refactoringTypes: RefactoringType[];
  scope: RefactoringScope;
  objectives: RefactoringObjective[];
  constraints: RefactoringConstraint[];
  qualityTargets: QualityTarget[];
}

export interface CreateRefactoringPlanResponse extends CreateResponse<RefactoringPlan> {
  data: RefactoringPlan;
  planId: string;
  refactoringActions: RefactoringAction[];
  impactAnalysis: RefactoringImpactAnalysis;
  riskAssessment: RefactoringRiskAssessment;
}

export interface ExecuteRefactoringRequest extends BaseApiRequest {
  planId: string;
  actionIds?: string[];
  executionStrategy: 'sequential' | 'parallel' | 'batch';
  validateChanges?: boolean;
  createBackup?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteRefactoringResponse extends BaseApiResponse<RefactoringExecution> {
  data: RefactoringExecution;
  executionId: string;
  status: RefactoringStatus;
  affectedFiles: FileChange[];
  backupLocation?: string;
}

export interface GetRefactoringResultsRequest extends GetRequest {
  executionId: string;
  includeChanges?: boolean;
  includeMetrics?: boolean;
  includeValidation?: boolean;
  includeQualityImpact?: boolean;
}

export interface GetRefactoringResultsResponse extends GetResponse<RefactoringResults> {
  data: RefactoringResults;
  changes: CodeChange[];
  metricsImprovement: MetricsImprovement;
  validation: RefactoringValidation;
  qualityImpact: QualityImpact;
}

// Architecture Transformation APIs
export interface CreateArchitectureTransformationRequest extends CreateRequest<ArchitectureTransformationData> {
  flowId: string;
  data: ArchitectureTransformationData;
  currentArchitecture: ArchitectureDescription;
  targetArchitecture: ArchitectureDescription;
  transformationStrategy: ArchitectureTransformationStrategy;
  migrationPatterns: MigrationPattern[];
  constraints: ArchitectureConstraint[];
}

export interface CreateArchitectureTransformationResponse extends CreateResponse<ArchitectureTransformation> {
  data: ArchitectureTransformation;
  transformationId: string;
  transformationPlan: ArchitectureTransformationPlan;
  migrationWaves: MigrationWave[];
  riskAssessment: ArchitectureRiskAssessment;
}

export interface GetArchitectureTransformationRequest extends GetRequest {
  transformationId: string;
  includeProgress?: boolean;
  includeDependencies?: boolean;
  includeImpactAnalysis?: boolean;
  includeValidation?: boolean;
}

export interface GetArchitectureTransformationResponse extends GetResponse<ArchitectureTransformation> {
  data: ArchitectureTransformation;
  progress: ArchitectureTransformationProgress;
  dependencies: ArchitectureDependency[];
  impactAnalysis: ArchitectureImpactAnalysis;
  validation: ArchitectureValidation;
}

export interface ExecuteArchitectureTransformationRequest extends BaseApiRequest {
  transformationId: string;
  waveIds?: string[];
  executionMode: 'simulation' | 'implementation' | 'rollback';
  validationEnabled?: boolean;
  monitoringEnabled?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteArchitectureTransformationResponse extends BaseApiResponse<ArchitectureTransformationExecution> {
  data: ArchitectureTransformationExecution;
  executionId: string;
  status: ArchitectureTransformationStatus;
  currentWave: MigrationWave;
  monitoringDashboard?: string;
}

// Technology Upgrade APIs
export interface CreateTechnologyUpgradeRequest extends CreateRequest<TechnologyUpgradeData> {
  flowId: string;
  data: TechnologyUpgradeData;
  currentTechnology: TechnologyStack;
  targetTechnology: TechnologyStack;
  upgradeStrategy: UpgradeStrategy;
  compatibilityRequirements: CompatibilityRequirement[];
  testingStrategy: TestingStrategy;
}

export interface CreateTechnologyUpgradeResponse extends CreateResponse<TechnologyUpgrade> {
  data: TechnologyUpgrade;
  upgradeId: string;
  upgradePlan: TechnologyUpgradePlan;
  compatibilityAnalysis: CompatibilityAnalysis;
  riskAssessment: UpgradeRiskAssessment;
}

export interface GetTechnologyUpgradeRequest extends GetRequest {
  upgradeId: string;
  includeCompatibility?: boolean;
  includeTestResults?: boolean;
  includePerformanceImpact?: boolean;
  includeSecurityImpact?: boolean;
}

export interface GetTechnologyUpgradeResponse extends GetResponse<TechnologyUpgrade> {
  data: TechnologyUpgrade;
  compatibility: CompatibilityStatus;
  testResults: UpgradeTestResults;
  performanceImpact: PerformanceImpact;
  securityImpact: SecurityImpact;
}

export interface ExecuteTechnologyUpgradeRequest extends BaseApiRequest {
  upgradeId: string;
  upgradePhase: 'preparation' | 'upgrade' | 'validation' | 'rollback';
  components?: string[];
  dryRun?: boolean;
  rollbackOnFailure?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteTechnologyUpgradeResponse extends BaseApiResponse<TechnologyUpgradeExecution> {
  data: TechnologyUpgradeExecution;
  executionId: string;
  status: UpgradeExecutionStatus;
  currentPhase: UpgradePhase;
  rollbackAvailable: boolean;
}

// Quality Assessment APIs
export interface AssessCodeQualityRequest extends BaseApiRequest {
  flowId: string;
  analysisId?: string;
  qualityFramework: QualityFramework;
  qualityStandards: QualityStandard[];
  metrics: QualityMetric[];
  thresholds: QualityThreshold[];
  includeRecommendations?: boolean;
  context: MultiTenantContext;
}

export interface AssessCodeQualityResponse extends BaseApiResponse<CodeQualityAssessment> {
  data: CodeQualityAssessment;
  assessmentId: string;
  overallScore: number;
  qualityGate: QualityGateResult;
  recommendations: QualityRecommendation[];
  trends: QualityTrend[];
}

export interface GetQualityMetricsRequest extends BaseApiRequest {
  flowId?: string;
  assessmentId?: string;
  metricTypes?: string[];
  timeRange?: {
    start: string;
    end: string;
  };
  aggregation?: 'avg' | 'min' | 'max' | 'latest';
  context: MultiTenantContext;
}

export interface GetQualityMetricsResponse extends BaseApiResponse<QualityMetrics> {
  data: QualityMetrics;
  trends: QualityMetricTrend[];
  benchmarks: QualityBenchmark[];
  violations: QualityViolation[];
}

// Testing and Validation APIs
export interface CreateModernizationTestSuiteRequest extends CreateRequest<TestSuiteData> {
  flowId: string;
  data: TestSuiteData;
  testTypes: TestType[];
  testScope: TestScope;
  testStrategy: TestStrategy;
  coverage: CoverageRequirement[];
  automation: TestAutomationConfig;
}

export interface CreateModernizationTestSuiteResponse extends CreateResponse<ModernizationTestSuite> {
  data: ModernizationTestSuite;
  testSuiteId: string;
  testPlan: TestPlan;
  automationPlan: TestAutomationPlan;
  estimatedDuration: number;
}

export interface ExecuteModernizationTestsRequest extends BaseApiRequest {
  testSuiteId: string;
  testCategories?: string[];
  executionMode: 'sequential' | 'parallel' | 'priority_based';
  continueOnFailure?: boolean;
  generateReport?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteModernizationTestsResponse extends BaseApiResponse<TestExecution> {
  data: TestExecution;
  executionId: string;
  status: TestExecutionStatus;
  estimatedCompletion: string;
  liveResults?: string;
}

export interface GetTestResultsRequest extends GetRequest {
  executionId: string;
  includeDetails?: boolean;
  includeFailures?: boolean;
  includeCoverage?: boolean;
  includePerformance?: boolean;
  testCategories?: string[];
}

export interface GetTestResultsResponse extends GetResponse<TestResults> {
  data: TestResults;
  summary: TestSummary;
  failures: TestFailure[];
  coverage: TestCoverage;
  performance: TestPerformance;
  recommendations: TestRecommendation[];
}

// Modernization Analytics and Reporting APIs
export interface GetModernizationAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  context: MultiTenantContext;
}

export interface GetModernizationAnalyticsResponse extends BaseApiResponse<ModernizationAnalytics> {
  data: ModernizationAnalytics;
  insights: ModernizationInsight[];
  trends: ModernizationTrend[];
  benchmarks: ModernizationBenchmark[];
  predictions: ModernizationPrediction[];
}

export interface GenerateModernizationReportRequest extends BaseApiRequest {
  flowId: string;
  reportType: 'progress' | 'quality' | 'transformation' | 'comprehensive';
  format: 'pdf' | 'html' | 'docx' | 'json';
  sections?: string[];
  includeCode?: boolean;
  includeMetrics?: boolean;
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateModernizationReportResponse extends BaseApiResponse<ModernizationReport> {
  data: ModernizationReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Supporting Data Types
export interface ModernizationFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  modernizationType: string;
  status: ModernizationStatus;
  priority: 'low' | 'medium' | 'high' | 'critical';
  scope: ModernizationScope;
  strategy: ModernizationStrategy;
  progress: number;
  phases: ModernizationPhases;
  currentPhase: string;
  targetArchitecture: TargetArchitecture;
  constraints: ModernizationConstraint[];
  objectives: ModernizationObjective[];
  clientAccountId: string;
  engagementId: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  metadata: Record<string, any>;
}

export interface ModernizationScope {
  applications: string[];
  components: string[];
  codebase: CodebaseScope;
  architecture: ArchitectureScope;
  technology: TechnologyScope;
  data: DataScope;
  integration: IntegrationScope;
  testing: TestingScope;
  deployment: DeploymentScope;
  monitoring: MonitoringScope;
}

export interface ModernizationStrategy {
  approach: 'big_bang' | 'phased' | 'strangler_fig' | 'parallel_run';
  pattern: 'lift_and_shift' | 'refactor' | 'replatform' | 'rebuild' | 'replace';
  prioritization: 'business_value' | 'technical_debt' | 'risk_reduction' | 'compliance';
  timeline: 'aggressive' | 'standard' | 'conservative';
  riskTolerance: 'low' | 'medium' | 'high';
  automation: 'manual' | 'semi_automated' | 'fully_automated';
  rollback: 'none' | 'checkpoint' | 'blue_green' | 'canary';
}

export interface ModernizationFlowConfiguration {
  qualityGates: QualityGate[];
  automation: AutomationConfiguration;
  testing: TestingConfiguration;
  monitoring: MonitoringConfiguration;
  security: SecurityConfiguration;
  compliance: ComplianceConfiguration;
  deployment: DeploymentConfiguration;
  rollback: RollbackConfiguration;
  reporting: ReportingConfiguration;
}

export interface ModernizationState {
  flowId: string;
  status: ModernizationStatus;
  currentPhase: string;
  phaseStates: Record<string, PhaseState>;
  analysisResults: Record<string, any>;
  transformationResults: Record<string, any>;
  qualityMetrics: QualityMetrics;
  riskStatus: RiskStatus;
  decisions: ModernizationDecision[];
  recommendations: ModernizationRecommendation[];
  blockers: ModernizationBlocker[];
  createdAt: string;
  updatedAt: string;
}

export type ModernizationStatus = 
  | 'planning' | 'analysis' | 'design' | 'transformation' 
  | 'testing' | 'validation' | 'deployment' | 'monitoring' 
  | 'completed' | 'failed' | 'cancelled' | 'on_hold';

export type TransformationType = 
  | 'language_migration' | 'framework_upgrade' | 'architecture_transformation' 
  | 'cloud_native' | 'microservices' | 'containerization' | 'serverless';

export type TransformationStatus = 
  | 'pending' | 'analyzing' | 'transforming' | 'validating' 
  | 'completed' | 'failed' | 'cancelled';

export type RefactoringType = 
  | 'extract_method' | 'extract_class' | 'inline_method' | 'move_method' 
  | 'rename_variable' | 'eliminate_dead_code' | 'simplify_conditional' 
  | 'consolidate_duplicate_conditional_fragments';

export type RefactoringStatus = 
  | 'planned' | 'executing' | 'validating' | 'completed' | 'failed' | 'rolled_back';

export type ArchitectureTransformationStatus = 
  | 'designing' | 'validating' | 'implementing' | 'testing' 
  | 'deploying' | 'monitoring' | 'completed' | 'failed';

export type UpgradeExecutionStatus = 
  | 'preparing' | 'upgrading' | 'validating' | 'completed' | 'failed' | 'rolled_back';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)