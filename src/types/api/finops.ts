/**
 * FinOps API Types
 * 
 * Type definitions for Financial Operations flow API endpoints, requests, and responses.
 * Covers cost optimization, budget management, resource optimization, and financial governance.
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
  UpdateResponse
} from './shared';

// FinOps Flow Management APIs
export interface InitializeFinOpsFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  finOpsScope: FinOpsScope;
  objectives: FinOpsObjective[];
  constraints: FinOpsConstraint[];
  governanceFramework: FinOpsGovernance;
  parentFlowId?: string;
  configuration?: FinOpsFlowConfiguration;
  metadata?: Record<string, any>;
}

export interface InitializeFinOpsFlowResponse extends BaseApiResponse<FinOpsFlowData> {
  data: FinOpsFlowData;
  flowId: string;
  initialState: FinOpsState;
  recommendedActions: FinOpsAction[];
  costBaseline: CostBaseline;
  optimizationOpportunities: OptimizationOpportunity[];
}

export interface GetFinOpsFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeCostAnalysis?: boolean;
  includeOptimizations?: boolean;
  includeBudgetStatus?: boolean;
  includeForecasts?: boolean;
  includeAlerts?: boolean;
}

export interface GetFinOpsFlowStatusResponse extends BaseApiResponse<FinOpsStatusDetail> {
  data: FinOpsStatusDetail;
  costAnalysis: CostAnalysis;
  optimizations: ActiveOptimization[];
  budgetStatus: BudgetStatus;
  forecasts: CostForecast[];
  alerts: FinOpsAlert[];
}

export interface ListFinOpsFlowsRequest extends ListRequest {
  finOpsTypes?: string[];
  status?: FinOpsStatus[];
  costCategories?: string[];
  optimizationTypes?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'cost_period_start' | 'cost_period_end';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
}

export interface ListFinOpsFlowsResponse extends ListResponse<FinOpsFlowSummary> {
  data: FinOpsFlowSummary[];
  aggregations?: FinOpsAggregation[];
  trends?: FinOpsTrend[];
  benchmarks?: FinOpsBenchmark[];
  portfolioMetrics?: FinOpsPortfolioMetrics;
}

// Cost Analysis APIs
export interface AnalyzeCostsRequest extends CreateRequest<CostAnalysisData> {
  flowId: string;
  data: CostAnalysisData;
  analysisType: 'current' | 'historical' | 'projected' | 'comparative';
  timeRange: {
    start: string;
    end: string;
  };
  granularity: 'hour' | 'day' | 'week' | 'month' | 'quarter' | 'year';
  dimensions: CostDimension[];
  filters: CostFilter[];
  includeBreakdown?: boolean;
  includeTrends?: boolean;
  includeAnomalies?: boolean;
}

export interface AnalyzeCostsResponse extends CreateResponse<CostAnalysisResult> {
  data: CostAnalysisResult;
  analysisId: string;
  totalCost: CostAmount;
  breakdown: CostBreakdown;
  trends: CostTrend[];
  anomalies: CostAnomaly[];
  insights: CostInsight[];
}

export interface GetCostAnalysisRequest extends GetRequest {
  analysisId: string;
  includeBreakdown?: boolean;
  includeTrends?: boolean;
  includeAnomalies?: boolean;
  includeComparisons?: boolean;
  includeRecommendations?: boolean;
  currency?: string;
}

export interface GetCostAnalysisResponse extends GetResponse<CostAnalysisResult> {
  data: CostAnalysisResult;
  detailedBreakdown: DetailedCostBreakdown;
  comparisons: CostComparison[];
  recommendations: CostRecommendation[];
  benchmarks: CostBenchmark[];
}

export interface CompareCostsRequest extends BaseApiRequest {
  analysisIds: string[];
  comparisonType: 'period_over_period' | 'budget_vs_actual' | 'plan_vs_actual' | 'benchmark';
  dimensions: CostDimension[];
  normalization?: CostNormalization;
  includeVariance?: boolean;
  context: MultiTenantContext;
}

export interface CompareCostsResponse extends BaseApiResponse<CostComparison> {
  data: CostComparison;
  comparisonId: string;
  variance: CostVariance;
  insights: ComparisonInsight[];
  recommendations: ComparisonRecommendation[];
}

// Budget Management APIs
export interface CreateBudgetRequest extends CreateRequest<BudgetData> {
  flowId: string;
  data: BudgetData;
  budgetType: 'operational' | 'project' | 'department' | 'service' | 'resource';
  period: BudgetPeriod;
  allocation: BudgetAllocation[];
  thresholds: BudgetThreshold[];
  approvals: BudgetApproval[];
  alerts: BudgetAlert[];
}

export interface CreateBudgetResponse extends CreateResponse<Budget> {
  data: Budget;
  budgetId: string;
  approvalStatus: BudgetApprovalStatus;
  trackingEnabled: boolean;
  alertsConfigured: boolean;
}

export interface GetBudgetStatusRequest extends GetRequest {
  budgetId: string;
  includeSpending?: boolean;
  includeForecasts?: boolean;
  includeVariance?: boolean;
  includeAlerts?: boolean;
  timeRange?: {
    start: string;
    end: string;
  };
}

export interface GetBudgetStatusResponse extends GetResponse<BudgetStatus> {
  data: BudgetStatus;
  spending: BudgetSpending;
  forecasts: BudgetForecast[];
  variance: BudgetVariance;
  alerts: BudgetAlert[];
  recommendations: BudgetRecommendation[];
}

export interface UpdateBudgetRequest extends UpdateRequest<Partial<BudgetData>> {
  budgetId: string;
  data: Partial<BudgetData>;
  updateType: 'allocation' | 'thresholds' | 'approvals' | 'alerts';
  reason?: string;
  approvalRequired?: boolean;
}

export interface UpdateBudgetResponse extends UpdateResponse<Budget> {
  data: Budget;
  changesApproved: boolean;
  impactAnalysis: BudgetImpactAnalysis;
  notifications: BudgetNotification[];
}

export interface ForecastBudgetRequest extends BaseApiRequest {
  budgetId: string;
  forecastHorizon: 'month' | 'quarter' | 'year';
  forecastMethod: 'linear' | 'exponential' | 'seasonal' | 'ml_based';
  includeScenarios?: boolean;
  confidence?: number;
  context: MultiTenantContext;
}

export interface ForecastBudgetResponse extends BaseApiResponse<BudgetForecast> {
  data: BudgetForecast;
  forecastId: string;
  scenarios: ForecastScenario[];
  confidence: number;
  methodology: string;
  assumptions: string[];
}

// Cost Optimization APIs
export interface IdentifyOptimizationsRequest extends BaseApiRequest {
  flowId: string;
  optimizationTypes: OptimizationType[];
  scope: OptimizationScope;
  constraints: OptimizationConstraint[];
  targets: OptimizationTarget[];
  riskTolerance: 'low' | 'medium' | 'high';
  includeAutomated?: boolean;
  context: MultiTenantContext;
}

export interface IdentifyOptimizationsResponse extends BaseApiResponse<OptimizationOpportunity[]> {
  data: OptimizationOpportunity[];
  totalPotentialSavings: CostAmount;
  highImpactOpportunities: OptimizationOpportunity[];
  quickWins: OptimizationOpportunity[];
  riskAssessment: OptimizationRiskAssessment;
}

export interface CreateOptimizationPlanRequest extends CreateRequest<OptimizationPlanData> {
  flowId: string;
  data: OptimizationPlanData;
  opportunities: string[];
  prioritization: OptimizationPrioritization;
  timeline: OptimizationTimeline;
  approvals: OptimizationApproval[];
  rollbackPlan?: RollbackPlan;
}

export interface CreateOptimizationPlanResponse extends CreateResponse<OptimizationPlan> {
  data: OptimizationPlan;
  planId: string;
  executionPlan: OptimizationExecutionPlan;
  riskMitigation: RiskMitigationPlan;
  approvalWorkflow: ApprovalWorkflow;
}

export interface ExecuteOptimizationRequest extends BaseApiRequest {
  planId: string;
  optimizationIds?: string[];
  executionMode: 'simulate' | 'implement' | 'rollback';
  approvalOverride?: boolean;
  monitoringEnabled?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteOptimizationResponse extends BaseApiResponse<OptimizationExecution> {
  data: OptimizationExecution;
  executionId: string;
  status: OptimizationExecutionStatus;
  estimatedSavings: CostAmount;
  monitoringDashboard?: string;
}

export interface GetOptimizationResultsRequest extends GetRequest {
  executionId: string;
  includeMetrics?: boolean;
  includeSavings?: boolean;
  includeImpact?: boolean;
  includeValidation?: boolean;
  timeRange?: {
    start: string;
    end: string;
  };
}

export interface GetOptimizationResultsResponse extends GetResponse<OptimizationResults> {
  data: OptimizationResults;
  actualSavings: CostAmount;
  impactAnalysis: OptimizationImpactAnalysis;
  validation: OptimizationValidation;
  recommendations: PostOptimizationRecommendation[];
}

// Resource Optimization APIs
export interface AnalyzeResourceUtilizationRequest extends BaseApiRequest {
  flowId: string;
  resourceTypes: ResourceType[];
  timeRange: {
    start: string;
    end: string;
  };
  metrics: UtilizationMetric[];
  thresholds: UtilizationThreshold[];
  includeRecommendations?: boolean;
  context: MultiTenantContext;
}

export interface AnalyzeResourceUtilizationResponse extends BaseApiResponse<ResourceUtilizationAnalysis> {
  data: ResourceUtilizationAnalysis;
  analysisId: string;
  utilizationSummary: UtilizationSummary;
  underutilizedResources: UnderutilizedResource[];
  overutilizedResources: OverutilizedResource[];
  recommendations: ResourceRecommendation[];
}

export interface OptimizeResourceAllocationRequest extends BaseApiRequest {
  analysisId: string;
  optimizationStrategy: ResourceOptimizationStrategy;
  constraints: ResourceConstraint[];
  objectives: ResourceObjective[];
  simulateOnly?: boolean;
  context: MultiTenantContext;
}

export interface OptimizeResourceAllocationResponse extends BaseApiResponse<ResourceOptimization> {
  data: ResourceOptimization;
  optimizationId: string;
  currentAllocation: ResourceAllocation;
  optimizedAllocation: ResourceAllocation;
  projectedSavings: CostAmount;
  implementationPlan: ResourceImplementationPlan;
}

export interface RightsizeResourcesRequest extends BaseApiRequest {
  flowId: string;
  resourceIds: string[];
  rightsizingStrategy: RightsizingStrategy;
  performanceRequirements: PerformanceRequirement[];
  costThresholds: CostThreshold[];
  dryRun?: boolean;
  context: MultiTenantContext;
}

export interface RightsizeResourcesResponse extends BaseApiResponse<RightsizingResult> {
  data: RightsizingResult;
  rightsizingId: string;
  recommendations: RightsizingRecommendation[];
  projectedSavings: CostAmount;
  performanceImpact: PerformanceImpact;
  implementationPlan: RightsizingImplementationPlan;
}

// Financial Governance APIs
export interface CreateCostGovernancePolicyRequest extends CreateRequest<CostGovernancePolicyData> {
  flowId: string;
  data: CostGovernancePolicyData;
  policyType: 'budget' | 'spending' | 'resource' | 'approval' | 'tagging';
  scope: GovernanceScope;
  rules: GovernanceRule[];
  enforcement: PolicyEnforcement;
  exceptions: PolicyException[];
}

export interface CreateCostGovernancePolicyResponse extends CreateResponse<CostGovernancePolicy> {
  data: CostGovernancePolicy;
  policyId: string;
  enforcementPlan: EnforcementPlan;
  complianceChecks: ComplianceCheck[];
  auditTrail: AuditTrail;
}

export interface ValidateCostGovernanceRequest extends BaseApiRequest {
  flowId: string;
  policyIds?: string[];
  validationType: 'realtime' | 'scheduled' | 'on_demand';
  scope: ValidationScope;
  includeRemediation?: boolean;
  context: MultiTenantContext;
}

export interface ValidateCostGovernanceResponse extends BaseApiResponse<GovernanceValidationResult> {
  data: GovernanceValidationResult;
  validationId: string;
  complianceScore: number;
  violations: PolicyViolation[];
  recommendations: ComplianceRecommendation[];
  remediationPlan: RemediationPlan;
}

export interface EnforceCostGovernanceRequest extends BaseApiRequest {
  policyId: string;
  enforcementAction: 'notify' | 'restrict' | 'terminate' | 'escalate';
  violationIds?: string[];
  overrideApproval?: string;
  gracePeriod?: number;
  context: MultiTenantContext;
}

export interface EnforceCostGovernanceResponse extends BaseApiResponse<EnforcementResult> {
  data: EnforcementResult;
  enforcementId: string;
  actionsExecuted: EnforcementAction[];
  exceptions: EnforcementException[];
  notifications: EnforcementNotification[];
}

// FinOps Analytics and Reporting APIs
export interface GetFinOpsAnalyticsRequest extends BaseApiRequest {
  flowId?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  metrics?: string[];
  dimensions?: string[];
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  currency?: string;
  includeForecasts?: boolean;
  context: MultiTenantContext;
}

export interface GetFinOpsAnalyticsResponse extends BaseApiResponse<FinOpsAnalytics> {
  data: FinOpsAnalytics;
  insights: FinOpsInsight[];
  trends: FinOpsTrend[];
  benchmarks: FinOpsBenchmark[];
  forecasts: FinOpsForecast[];
  kpis: FinOpsKPI[];
}

export interface GenerateFinOpsReportRequest extends BaseApiRequest {
  flowId: string;
  reportType: 'cost_analysis' | 'budget_performance' | 'optimization' | 'governance' | 'executive';
  format: 'pdf' | 'html' | 'docx' | 'xlsx' | 'json';
  timeRange?: {
    start: string;
    end: string;
  };
  sections?: string[];
  currency?: string;
  customizations?: ReportCustomization;
  context: MultiTenantContext;
}

export interface GenerateFinOpsReportResponse extends BaseApiResponse<FinOpsReport> {
  data: FinOpsReport;
  reportId: string;
  downloadUrl: string;
  expiresAt: string;
}

// Cost Allocation and Chargeback APIs
export interface ConfigureCostAllocationRequest extends CreateRequest<CostAllocationConfiguration> {
  flowId: string;
  data: CostAllocationConfiguration;
  allocationMethod: 'direct' | 'proportional' | 'activity_based' | 'shared_services';
  allocationRules: AllocationRule[];
  costPools: CostPool[];
  chargebackModel: ChargebackModel;
}

export interface ConfigureCostAllocationResponse extends CreateResponse<CostAllocation> {
  data: CostAllocation;
  allocationId: string;
  validationResults: AllocationValidationResult[];
  scheduleEnabled: boolean;
  reportingEnabled: boolean;
}

export interface ExecuteCostAllocationRequest extends BaseApiRequest {
  allocationId: string;
  period: {
    start: string;
    end: string;
  };
  dryRun?: boolean;
  includeApprovals?: boolean;
  context: MultiTenantContext;
}

export interface ExecuteCostAllocationResponse extends BaseApiResponse<CostAllocationExecution> {
  data: CostAllocationExecution;
  executionId: string;
  allocatedCosts: AllocatedCost[];
  chargebacks: Chargeback[];
  approvals: AllocationApproval[];
}

export interface GetChargebackReportRequest extends BaseApiRequest {
  flowId: string;
  period: {
    start: string;
    end: string;
  };
  recipients?: string[];
  costCategories?: string[];
  includeDetails?: boolean;
  format?: 'summary' | 'detailed' | 'itemized';
  context: MultiTenantContext;
}

export interface GetChargebackReportResponse extends BaseApiResponse<ChargebackReport> {
  data: ChargebackReport;
  reportId: string;
  chargebacks: ChargebackDetail[];
  summary: ChargebackSummary;
  approvals: ChargebackApproval[];
}

// Supporting Data Types
export interface FinOpsFlowData {
  id: string;
  flowId: string;
  flowName: string;
  flowDescription?: string;
  finOpsType: string;
  status: FinOpsStatus;
  priority: 'low' | 'medium' | 'high' | 'critical';
  scope: FinOpsScope;
  objectives: FinOpsObjective[];
  constraints: FinOpsConstraint[];
  governance: FinOpsGovernance;
  progress: number;
  phases: FinOpsPhases;
  currentPhase: string;
  clientAccountId: string;
  engagementId: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  metadata: Record<string, any>;
}

export interface FinOpsScope {
  accounts: string[];
  services: string[];
  resources: string[];
  regions: string[];
  costCenters: string[];
  projects: string[];
  environments: string[];
  timeframe: {
    start: string;
    end: string;
  };
  budget: {
    amount: number;
    currency: string;
  };
  exclusions?: string[];
  tags?: Record<string, string>;
}

export interface FinOpsObjective {
  id: string;
  name: string;
  description: string;
  type: 'cost_reduction' | 'budget_compliance' | 'resource_optimization' | 'governance';
  target: ObjectiveTarget;
  priority: number;
  deadline?: string;
  measurable: boolean;
  kpis: string[];
}

export interface FinOpsConstraint {
  id: string;
  type: 'budget' | 'performance' | 'compliance' | 'operational';
  description: string;
  value: any;
  operator: string;
  mandatory: boolean;
  exceptions?: string[];
}

export interface FinOpsGovernance {
  framework: string;
  policies: string[];
  approvalWorkflows: ApprovalWorkflow[];
  complianceRequirements: string[];
  auditFrequency: string;
  reportingCadence: string;
  stakeholders: Stakeholder[];
  escalationPaths: EscalationPath[];
}

export interface FinOpsFlowConfiguration {
  automation: FinOpsAutomation;
  monitoring: FinOpsMonitoring;
  alerting: FinOpsAlerting;
  reporting: FinOpsReporting;
  optimization: FinOpsOptimization;
  governance: FinOpsGovernanceConfig;
  integration: FinOpsIntegration;
}

export interface FinOpsState {
  flowId: string;
  status: FinOpsStatus;
  currentPhase: string;
  phaseStates: Record<string, PhaseState>;
  costBaseline: CostBaseline;
  budgetStatus: BudgetStatus;
  optimizationStatus: OptimizationStatus;
  governanceStatus: GovernanceStatus;
  kpis: FinOpsKPI[];
  alerts: FinOpsAlert[];
  recommendations: FinOpsRecommendation[];
  decisions: FinOpsDecision[];
  createdAt: string;
  updatedAt: string;
}

export type FinOpsStatus = 
  | 'planning' | 'baseline_analysis' | 'budget_setup' | 'optimization_identification'
  | 'implementation' | 'monitoring' | 'governance' | 'reporting'
  | 'completed' | 'paused' | 'failed' | 'cancelled';

export type OptimizationType = 
  | 'rightsizing' | 'scheduling' | 'purchasing_options' | 'architecture'
  | 'resource_cleanup' | 'storage_optimization' | 'network_optimization';

export type OptimizationExecutionStatus = 
  | 'planned' | 'simulating' | 'approved' | 'implementing'
  | 'monitoring' | 'completed' | 'failed' | 'rolled_back';

// Additional supporting interfaces would continue here...
// (This is a comprehensive but truncated version for brevity)