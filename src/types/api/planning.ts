/**
 * Planning API Types
 * 
 * Type definitions for Migration Planning flow API endpoints, requests, and responses.
 * Covers migration strategy, resource planning, timeline estimation, and execution planning.
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

// Planning Flow Management APIs
export interface InitializePlanningFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  planningScope: PlanningScope;
  assessmentInputs: AssessmentInput[];
  targetArchitecture: TargetArchitecture;
  constraints: PlanningConstraint[];
  objectives: PlanningObjective[];
  parentFlowId?: string;
  configuration?: PlanningFlowConfiguration;
  template?: string;
  metadata?: Record<string, any>;
}

export interface InitializePlanningFlowResponse extends BaseApiResponse<PlanningFlowData> {
  data: PlanningFlowData;
  flowId: string;
  initialState: PlanningState;
  planningFramework: PlanningFramework;
  nextSteps: string[];
  recommendations?: string[];
}

export interface GetPlanningFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeTimeline?: boolean;
  includeResources?: boolean;
  includeRisks?: boolean;
  includeCosts?: boolean;
  includeDeliverables?: boolean;
}

export interface GetPlanningFlowStatusResponse extends BaseApiResponse<PlanningStatusDetail> {
  data: PlanningStatusDetail;
  timeline: PlanningTimeline;
  resources: ResourcePlan;
  risks: RiskRegister;
  costs: CostPlan;
  realTimeUpdates?: boolean;
  nextRefresh?: string;
}

export interface ListPlanningFlowsRequest extends ListRequest {
  planningTypes?: string[];
  status?: PlanningStatus[];
  priorities?: string[];
  complexityLevels?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'completed' | 'planned_start' | 'planned_end';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
  includeCosts?: boolean;
}

export interface ListPlanningFlowsResponse extends ListResponse<PlanningFlowSummary> {
  data: PlanningFlowSummary[];
  aggregations?: PlanningAggregation[];
  trends?: PlanningTrend[];
  portfolioMetrics?: PortfolioMetrics;
}

export interface UpdatePlanningFlowRequest extends UpdateRequest<Partial<PlanningFlowData>> {
  flowId: string;
  data: Partial<PlanningFlowData>;
  validateDependencies?: boolean;
  recalculateTimeline?: boolean;
  updateResourceAllocation?: boolean;
  updateCosts?: boolean;
  propagateChanges?: boolean;
}

export interface UpdatePlanningFlowResponse extends UpdateResponse<PlanningFlowData> {
  data: PlanningFlowData;
  impactAnalysis?: ChangeImpactAnalysis;
  timelineUpdates?: TimelineUpdate[];
  resourceUpdates?: ResourceUpdate[];
  costUpdates?: CostUpdate[];
}

// Migration Strategy APIs
export interface CreateMigrationStrategyRequest extends CreateRequest<MigrationStrategyData> {
  flowId: string;
  data: MigrationStrategyData;
  assessmentInputs: AssessmentInput[];
  businessDrivers: BusinessDriver[];
  constraints: StrategyConstraint[];
  successCriteria: SuccessCriteria[];
  generateAlternatives?: boolean;
  includeRiskAnalysis?: boolean;
  includeCostAnalysis?: boolean;
}

export interface CreateMigrationStrategyResponse extends CreateResponse<MigrationStrategyResult> {
  data: MigrationStrategyResult;
  strategyId: string;
  alternatives: MigrationAlternative[];
  riskAnalysis?: StrategyRiskAnalysis;
  costAnalysis?: StrategyCostAnalysis;
  feasibilityAssessment: FeasibilityAssessment;
}

export interface GetMigrationStrategyRequest extends GetRequest {
  strategyId: string;
  includeDetails?: boolean;
  includeAlternatives?: boolean;
  includeAnalysis?: boolean;
  includeComparison?: boolean;
}

export interface GetMigrationStrategyResponse extends GetResponse<MigrationStrategyResult> {
  data: MigrationStrategyResult;
  detailedAnalysis: StrategyAnalysis;
  comparisonMatrix?: StrategyComparison;
  recommendations: StrategyRecommendation[];
}

export interface CompareMigrationStrategiesRequest extends BaseApiRequest {
  strategyIds: string[];
  comparisonCriteria: ComparisonCriteria[];
  weightings?: Record<string, number>;
  includeScoring?: boolean;
  context: MultiTenantContext;
}

export interface CompareMigrationStrategiesResponse extends BaseApiResponse<StrategyComparison> {
  data: StrategyComparison;
  scoredComparison?: ScoredComparison;
  recommendation: string;
  reasoning: string;
}

// Timeline Planning APIs
export interface CreateTimelinePlanRequest extends CreateRequest<TimelinePlanData> {
  flowId: string;
  strategyId: string;
  data: TimelinePlanData;
  planningHorizon: PlanningHorizon;
  dependencies: TimelineDependency[];
  resources: ResourceAvailability[];
  constraints: TimelineConstraint[];
  milestones: Milestone[];
  includeBuffers?: boolean;
  includeRiskMitigation?: boolean;
}

export interface CreateTimelinePlanResponse extends CreateResponse<TimelinePlanResult> {
  data: TimelinePlanResult;
  timelineId: string;
  criticalPath: CriticalPathAnalysis;
  resourceConflicts?: ResourceConflict[];
  riskMitigationTime?: number;
  feasibilityCheck: TimelineFeasibility;
}

export interface GetTimelinePlanRequest extends GetRequest {
  timelineId: string;
  viewType?: 'gantt' | 'calendar' | 'kanban' | 'milestone';
  granularity?: 'day' | 'week' | 'month' | 'quarter';
  includeDetails?: boolean;
  includeDependencies?: boolean;
  includeResources?: boolean;
  includeRisks?: boolean;
}

export interface GetTimelinePlanResponse extends GetResponse<TimelinePlanResult> {
  data: TimelinePlanResult;
  visualization: TimelineVisualization;
  criticalPath: CriticalPathAnalysis;
  slackAnalysis: SlackAnalysis;
  resourceUtilization: ResourceUtilization;
}

export interface UpdateTimelinePlanRequest extends UpdateRequest<Partial<TimelinePlanData>> {
  timelineId: string;
  data: Partial<TimelinePlanData>;
  recalculateCriticalPath?: boolean;
  validateConstraints?: boolean;
  updateResourceAllocation?: boolean;
  propagateChanges?: boolean;
}

export interface UpdateTimelinePlanResponse extends UpdateResponse<TimelinePlanResult> {
  data: TimelinePlanResult;
  impactAnalysis: TimelineImpactAnalysis;
  newCriticalPath?: CriticalPathAnalysis;
  resourceImpacts?: ResourceImpact[];
  constraintViolations?: ConstraintViolation[];
}

// Resource Planning APIs
export interface CreateResourcePlanRequest extends CreateRequest<ResourcePlanData> {
  flowId: string;
  timelineId?: string;
  data: ResourcePlanData;
  resourceTypes: ResourceType[];
  skillRequirements: SkillRequirement[];
  availabilityConstraints: AvailabilityConstraint[];
  budgetConstraints: BudgetConstraint[];
  includeOptimization?: boolean;
  includeSkillsGapAnalysis?: boolean;
}

export interface CreateResourcePlanResponse extends CreateResponse<ResourcePlanResult> {
  data: ResourcePlanResult;
  resourcePlanId: string;
  optimization?: ResourceOptimization;
  skillsGapAnalysis?: SkillsGapAnalysis;
  costProjection: CostProjection;
  feasibilityAssessment: ResourceFeasibility;
}

export interface GetResourcePlanRequest extends GetRequest {
  resourcePlanId: string;
  includeUtilization?: boolean;
  includeSkillsAnalysis?: boolean;
  includeCostAnalysis?: boolean;
  includeOptimization?: boolean;
  timeRange?: {
    start: string;
    end: string;
  };
}

export interface GetResourcePlanResponse extends GetResponse<ResourcePlanResult> {
  data: ResourcePlanResult;
  utilizationAnalysis: UtilizationAnalysis;
  skillsAnalysis: SkillsAnalysis;
  costAnalysis: ResourceCostAnalysis;
  optimizationOpportunities: OptimizationOpportunity[];
}

export interface OptimizeResourceAllocationRequest extends BaseApiRequest {
  resourcePlanId: string;
  optimizationCriteria: OptimizationCriteria[];
  constraints: OptimizationConstraint[];
  objectives: OptimizationObjective[];
  algorithm?: 'genetic' | 'simulated_annealing' | 'linear_programming' | 'heuristic';
  context: MultiTenantContext;
}

export interface OptimizeResourceAllocationResponse extends BaseApiResponse<ResourceOptimizationResult> {
  data: ResourceOptimizationResult;
  optimizedPlan: ResourcePlanResult;
  improvements: OptimizationImprovement[];
  scenarios: OptimizationScenario[];
}

// Risk Planning APIs
export interface CreateRiskPlanRequest extends CreateRequest<RiskPlanData> {
  flowId: string;
  data: RiskPlanData;
  riskCategories: RiskCategory[];
  riskTolerance: RiskTolerance;
  mitigationStrategies: MitigationStrategy[];
  contingencyPlanning: ContingencyPlan[];
  includeQuantification?: boolean;
  includeSimulation?: boolean;
}

export interface CreateRiskPlanResponse extends CreateResponse<RiskPlanResult> {
  data: RiskPlanResult;
  riskPlanId: string;
  riskRegister: RiskRegister;
  quantification?: RiskQuantification;
  simulationResults?: RiskSimulation;
  mitigationEffectiveness: MitigationEffectiveness;
}

export interface GetRiskPlanRequest extends GetRequest {
  riskPlanId: string;
  includeQuantification?: boolean;
  includeSimulation?: boolean;
  includeMitigation?: boolean;
  includeContingency?: boolean;
  riskCategories?: string[];
}

export interface GetRiskPlanResponse extends GetResponse<RiskPlanResult> {
  data: RiskPlanResult;
  riskMatrix: RiskMatrix;
  heatMap: RiskHeatMap;
  mitigationPlan: ComprehensiveMitigationPlan;
  contingencyPlans: ContingencyPlan[];
}

export interface SimulateRiskScenariosRequest extends BaseApiRequest {
  riskPlanId: string;
  scenarios: RiskScenario[];
  simulationConfig: SimulationConfig;
  iterations?: number;
  confidenceLevel?: number;
  context: MultiTenantContext;
}

export interface SimulateRiskScenariosResponse extends BaseApiResponse<RiskSimulationResult> {
  data: RiskSimulationResult;
  scenarios: ScenarioResult[];
  probabilityDistributions: ProbabilityDistribution[];
  recommendedActions: RiskAction[];
}

// Cost Planning APIs
export interface CreateCostPlanRequest extends CreateRequest<CostPlanData> {
  flowId: string;
  data: CostPlanData;
  costModel: CostModel;
  assumptions: CostAssumption[];
  scenarios: CostScenario[];
  includeOptimization?: boolean;
  includeSensitivityAnalysis?: boolean;
  includeROIAnalysis?: boolean;
}

export interface CreateCostPlanResponse extends CreateResponse<CostPlanResult> {
  data: CostPlanResult;
  costPlanId: string;
  totalCostEstimate: CostEstimate;
  breakdown: CostBreakdown;
  scenarios: CostScenarioResult[];
  optimization?: CostOptimization;
}

export interface GetCostPlanRequest extends GetRequest {
  costPlanId: string;
  includeBreakdown?: boolean;
  includeScenarios?: boolean;
  includeSensitivity?: boolean;
  includeROI?: boolean;
  currency?: string;
  timeframe?: {
    start: string;
    end: string;
  };
}

export interface GetCostPlanResponse extends GetResponse<CostPlanResult> {
  data: CostPlanResult;
  detailedBreakdown: DetailedCostBreakdown;
  sensitivityAnalysis: SensitivityAnalysis;
  roiAnalysis: ROIAnalysis;
  benchmarks: CostBenchmark[];
}

export interface OptimizeCostPlanRequest extends BaseApiRequest {
  costPlanId: string;
  optimizationTargets: CostOptimizationTarget[];
  constraints: CostConstraint[];
  tradeoffs: CostTradeoff[];
  includeAlternatives?: boolean;
  context: MultiTenantContext;
}

export interface OptimizeCostPlanResponse extends BaseApiResponse<CostOptimizationResult> {
  data: CostOptimizationResult;
  optimizedPlan: CostPlanResult;
  savings: CostSaving[];
  alternatives: CostAlternative[];
  recommendations: CostRecommendation[];
}

// Execution Planning APIs
export interface CreateExecutionPlanRequest extends CreateRequest<ExecutionPlanData> {
  flowId: string;
  data: ExecutionPlanData;
  workstreams: Workstream[];
  deliverables: Deliverable[];
  governance: GovernanceFramework;
  qualityGates: QualityGate[];
  communicationPlan: CommunicationPlan;
  includeDetailedTasks?: boolean;
  includeResourceAssignment?: boolean;
}

export interface CreateExecutionPlanResponse extends CreateResponse<ExecutionPlanResult> {
  data: ExecutionPlanResult;
  executionPlanId: string;
  workBreakdownStructure: WorkBreakdownStructure;
  resourceAssignments?: ResourceAssignment[];
  governanceStructure: GovernanceStructure;
}

export interface GetExecutionPlanRequest extends GetRequest {
  executionPlanId: string;
  includeWorkstreams?: boolean;
  includeDeliverables?: boolean;
  includeGovernance?: boolean;
  includeQualityGates?: boolean;
  includeCommunication?: boolean;
  includeRisks?: boolean;
}

export interface GetExecutionPlanResponse extends GetResponse<ExecutionPlanResult> {
  data: ExecutionPlanResult;
  workstreamDetails: WorkstreamDetail[];
  deliverableStatus: DeliverableStatus[];
  governanceHealth: GovernanceHealth;
  qualityMetrics: QualityMetrics;
}

// Plan Validation and Approval APIs
export interface ValidatePlanRequest extends BaseApiRequest {
  planId: string;
  planType: 'migration_strategy' | 'timeline' | 'resource' | 'risk' | 'cost' | 'execution';
  validationCriteria: ValidationCriteria[];
  includeConstraintCheck?: boolean;
  includeFeasibilityCheck?: boolean;
  includeComplianceCheck?: boolean;
  context: MultiTenantContext;
}

export interface ValidatePlanResponse extends BaseApiResponse<PlanValidationResult> {
  data: PlanValidationResult;
  isValid: boolean;
  validationErrors: PlanValidationError[];
  validationWarnings: PlanValidationWarning[];
  constraintViolations: ConstraintViolation[];
  feasibilityIssues: FeasibilityIssue[];
  complianceIssues: ComplianceIssue[];
}

export interface ApprovePlanRequest extends BaseApiRequest {
  planId: string;
  planType: string;
  approvalLevel: 'technical' | 'business' | 'executive' | 'governance';
  approverComments?: string;
  conditions?: ApprovalCondition[];
  context: MultiTenantContext;
}

export interface ApprovePlanResponse extends BaseApiResponse<PlanApprovalResult> {
  data: PlanApprovalResult;
  approvalId: string;
  status: 'approved' | 'approved_with_conditions' | 'rejected' | 'needs_revision';
  nextSteps: string[];
  conditions: ApprovalCondition[];
}

// Plan Analytics and Reporting APIs
export interface GetPlanningAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  planIds?: string[];
  planTypes?: string[];
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  context: MultiTenantContext;
}

export interface GetPlanningAnalyticsResponse extends BaseApiResponse<PlanningAnalytics> {
  data: PlanningAnalytics;
  insights: PlanningInsight[];
  trends: PlanningTrend[];
  benchmarks: PlanningBenchmark[];
  predictions: PlanningPrediction[];
}

export interface GeneratePlanningReportRequest extends BaseApiRequest {
  planId: string;
  planType: string;
  reportType: 'executive' | 'detailed' | 'stakeholder' | 'governance';
  format: 'pdf' | 'html' | 'docx' | 'pptx';
  sections?: string[];
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GeneratePlanningReportResponse extends BaseApiResponse<PlanningReport> {
  data: PlanningReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Supporting Data Types
export interface PlanningFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  planningType: string;
  status: PlanningStatus;
  priority: 'low' | 'medium' | 'high' | 'critical';
  scope: PlanningScope;
  progress: number;
  phases: PlanningPhases;
  currentPhase: string;
  targetArchitecture: TargetArchitecture;
  constraints: PlanningConstraint[];
  objectives: PlanningObjective[];
  clientAccountId: string;
  engagementId: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  approvedAt?: string;
  metadata: Record<string, any>;
}

export interface PlanningScope {
  applications: string[];
  infrastructure: string[];
  data: string[];
  processes: string[];
  geography: string[];
  businessUnits: string[];
  timeframe: {
    start: string;
    end: string;
  };
  budget: {
    min: number;
    max: number;
    currency: string;
  };
  resources: {
    internal: number;
    external: number;
    skills: string[];
  };
  exclusions?: string[];
  assumptions?: string[];
}

export interface PlanningFlowConfiguration {
  methodology: 'agile' | 'waterfall' | 'hybrid' | 'lean' | 'devops';
  governanceFramework: string;
  qualityStandards: string[];
  riskManagement: boolean;
  changeManagement: boolean;
  communicationProtocols: string[];
  reportingFrequency: string;
  approvalGates: string[];
  integrations: IntegrationConfig[];
  automation: AutomationConfig[];
}

export interface PlanningState {
  flowId: string;
  currentPhase: string;
  nextPhase?: string;
  phaseCompletion: Record<string, boolean>;
  phaseResults: Record<string, any>;
  planningArtifacts: Record<string, any>;
  approvalStatus: Record<string, string>;
  riskStatus: RiskStatus;
  resourceStatus: ResourceStatus;
  timelineStatus: TimelineStatus;
  costStatus: CostStatus;
  qualityStatus: QualityStatus;
  blockers: PlanningBlocker[];
  dependencies: PlanningDependency[];
  assumptions: PlanningAssumption[];
  decisions: PlanningDecision[];
  createdAt: string;
  updatedAt: string;
}

export type PlanningStatus = 
  | 'initiation' | 'strategy_development' | 'timeline_planning' 
  | 'resource_planning' | 'risk_planning' | 'cost_planning' 
  | 'execution_planning' | 'validation' | 'approval' 
  | 'approved' | 'rejected' | 'on_hold' | 'cancelled';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)