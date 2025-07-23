/**
 * Observability Flow Management Types
 * 
 * Type definitions for initializing, managing, and tracking observability flows.
 * Handles flow lifecycle, status monitoring, and flow listing operations.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ListRequest,
  ListResponse,
  GetRequest
} from '../shared';
import type { ObservabilityScope, MonitoringStrategy, ObservabilityStatus, ObservabilityFlowData, PerformanceMetrics } from './core-types'
import type { ObservabilityObjective, ObservabilityRequirement } from './core-types'

// Flow Initialization
export interface InitializeObservabilityFlowRequest extends BaseApiRequest {
  flowName: string;
  flowDescription?: string;
  context: MultiTenantContext;
  observabilityScope: ObservabilityScope;
  monitoringStrategy: MonitoringStrategy;
  objectives: ObservabilityObjective[];
  requirements: ObservabilityRequirement[];
  parentFlowId?: string;
  configuration?: ObservabilityFlowConfiguration;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface InitializeObservabilityFlowResponse extends BaseApiResponse<ObservabilityFlowData> {
  data: ObservabilityFlowData;
  flowId: string;
  initialState: ObservabilityState;
  monitoringPlan: MonitoringPlan;
  recommendations: ObservabilityRecommendation[];
  baselineMetrics: BaselineMetrics;
}

// Flow Status Management
export interface GetObservabilityFlowStatusRequest extends GetRequest {
  flowId: string;
  includeDetails?: boolean;
  includeMetrics?: boolean;
  includeAlerts?: boolean;
  includeDashboards?: boolean;
  includeHealth?: boolean;
  includePerformance?: boolean;
}

export interface GetObservabilityFlowStatusResponse extends BaseApiResponse<ObservabilityStatusDetail> {
  data: ObservabilityStatusDetail;
  metrics: ObservabilityMetrics;
  alerts: Alert[];
  dashboards: Dashboard[];
  healthStatus: HealthStatus;
  performance: PerformanceMetrics;
}

// Flow Listing
export interface ListObservabilityFlowsRequest extends ListRequest {
  observabilityTypes?: string[];
  status?: ObservabilityStatus[];
  monitoringLevels?: string[];
  healthStates?: string[];
  clientAccountIds?: string[];
  engagementIds?: string[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'updated' | 'last_monitored' | 'last_alert';
  };
  includeArchived?: boolean;
  includeMetrics?: boolean;
}

export interface ListObservabilityFlowsResponse extends ListResponse<ObservabilityFlowSummary> {
  data: ObservabilityFlowSummary[];
  aggregations?: ObservabilityAggregation[];
  trends?: ObservabilityTrend[];
  healthOverview?: HealthOverview;
}

// Supporting Types

export interface ObservabilityFlowConfiguration {
  autoScaling: boolean;
  alertingEnabled: boolean;
  retentionPeriod: string;
  samplingRate: number;
  costOptimization: boolean;
}

export interface ObservabilityState {
  phase: string;
  progress: number;
  healthScore: number;
  lastUpdate: string;
  issues: ObservabilityIssue[];
}

export interface MonitoringPlan {
  phases: PlanPhase[];
  timeline: string;
  resources: ResourceRequirement[];
  dependencies: string[];
}

export interface ObservabilityRecommendation {
  id: string;
  type: 'optimization' | 'configuration' | 'alerting' | 'dashboard';
  title: string;
  description: string;
  impact: 'low' | 'medium' | 'high';
  effort: 'low' | 'medium' | 'high';
  priority: number;
}

export interface BaselineMetrics {
  availability: number;
  responseTime: number;
  errorRate: number;
  throughput: number;
  timestamp: string;
}

export interface ObservabilityStatusDetail {
  flowId: string;
  currentPhase: string;
  overallHealth: 'healthy' | 'warning' | 'critical' | 'unknown';
  activeAlerts: number;
  lastMonitored: string;
  uptime: number;
}

export interface ObservabilityMetrics {
  availability: number;
  performance: PerformanceMetrics;
  reliability: ReliabilityMetrics;
  security: SecurityMetrics;
}

export interface Alert {
  id: string;
  ruleId: string;
  severity: 'info' | 'warning' | 'minor' | 'major' | 'critical' | 'blocker';
  status: 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'closed';
  title: string;
  description: string;
  firedAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
}

export interface Dashboard {
  id: string;
  name: string;
  type: 'operational' | 'executive' | 'technical' | 'business' | 'custom';
  url: string;
  lastUpdated: string;
}

export interface HealthStatus {
  overall: 'healthy' | 'warning' | 'critical' | 'unknown';
  components: ComponentHealth[];
  score: number;
  lastCheck: string;
}

// PerformanceMetrics imported from core-types

export interface ObservabilityFlowSummary {
  id: string;
  flowId: string;
  name: string;
  type: string;
  status: ObservabilityStatus;
  health: 'healthy' | 'warning' | 'critical' | 'unknown';
  lastActivity: string;
  alertCount: number;
}

export interface ObservabilityAggregation {
  name: string;
  type: 'terms' | 'date_histogram' | 'range' | 'stats' | 'cardinality';
  field: string;
  buckets: AggregationBucket[];
}

export interface ObservabilityTrend {
  metric: string;
  direction: 'up' | 'down' | 'stable';
  percentage: number;
  period: string;
}

export interface HealthOverview {
  totalFlows: number;
  healthyFlows: number;
  warningFlows: number;
  criticalFlows: number;
  overallScore: number;
}

// Additional supporting interfaces
export interface ObservabilityIssue {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  createdAt: string;
}

export interface PlanPhase {
  name: string;
  duration: string;
  dependencies: string[];
  tasks: string[];
}

export interface ResourceRequirement {
  type: 'compute' | 'storage' | 'network' | 'license';
  amount: number;
  unit: string;
}

export interface ReliabilityMetrics {
  mttr: number;
  mtbf: number;
  uptime: number;
  slaCompliance: number;
}

export interface SecurityMetrics {
  vulnerabilities: number;
  threats: number;
  complianceScore: number;
  lastScan: string;
}

export interface ComponentHealth {
  component: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  score: number;
  lastCheck: string;
}

export interface AggregationBucket {
  key: string;
  count: number;
  percentage: number;
}