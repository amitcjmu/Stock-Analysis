/**
 * Discovery Crew Analysis API Types
 *
 * Type definitions for AI crew analysis operations including analysis execution,
 * findings, recommendations, and implementation planning.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  GetRequest,
  GetResponse,
  ListRequest,
  ListResponse,
  MultiTenantContext
} from '../shared';

// Crew Analysis APIs
export interface TriggerCrewAnalysisRequest extends BaseApiRequest {
  flowId: string;
  context: MultiTenantContext;
  analysisType: AnalysisType;
  parameters?: AnalysisParameters;
  targetScope?: AnalysisScope;
  priority?: 'low' | 'medium' | 'high' | 'urgent';
}

export interface TriggerCrewAnalysisResponse extends BaseApiResponse<AnalysisJob> {
  data: AnalysisJob;
  analysisId: string;
  estimatedCompletion?: string;
  dependencies?: string[];
}

export interface GetCrewAnalysisRequest extends GetRequest {
  analysisId: string;
  includeDetails?: boolean;
  includeRecommendations?: boolean;
  includeMetadata?: boolean;
}

export interface GetCrewAnalysisResponse extends GetResponse<CrewAnalysisResult> {
  data: CrewAnalysisResult;
  relatedAnalyses?: RelatedAnalysis[];
  actionableInsights?: ActionableInsight[];
}

export interface ListCrewAnalysesRequest extends ListRequest {
  flowId: string;
  analysisType?: AnalysisType[];
  status?: AnalysisStatus[];
  dateRange?: {
    start: string;
    end: string;
    field: 'created' | 'completed';
  };
  includeMetrics?: boolean;
}

export interface ListCrewAnalysesResponse extends ListResponse<CrewAnalysisSummary> {
  data: CrewAnalysisSummary[];
  trendData?: AnalysisTrend[];
  performanceMetrics?: AnalysisPerformanceMetrics;
}

export interface GetAnalysisRecommendationsRequest extends GetRequest {
  analysisId: string;
  category?: RecommendationCategory[];
  priority?: RecommendationPriority[];
  implementationDifficulty?: ImplementationDifficulty[];
}

export interface GetAnalysisRecommendationsResponse extends ListResponse<AnalysisRecommendation> {
  data: AnalysisRecommendation[];
  prioritizedList: string[];
  implementationPlan?: ImplementationPlan;
}

// Crew Analysis Models
export interface CrewAnalysisResult {
  id: string;
  flowId: string;
  analysisType: AnalysisType;
  status: AnalysisStatus;
  findings: AnalysisFinding[];
  recommendations: AnalysisRecommendation[];
  confidence: number;
  quality: number;
  executedAt: string;
  completedAt?: string;
  executedBy: string;
  parameters: AnalysisParameters;
  scope: AnalysisScope;
  metrics: AnalysisMetrics;
  metadata: Record<string, string | number | boolean | null>;
}

export interface CrewAnalysisSummary {
  id: string;
  analysisType: AnalysisType;
  status: AnalysisStatus;
  confidence: number;
  findingsCount: number;
  recommendationsCount: number;
  executedAt: string;
  completedAt?: string;
  executionTime?: number;
}

export interface AnalysisJob {
  id: string;
  flowId: string;
  analysisType: AnalysisType;
  status: AnalysisStatus;
  progress: number;
  parameters: AnalysisParameters;
  scope: AnalysisScope;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  estimatedDuration?: number;
  resourceAllocation?: ResourceAllocation;
}

export interface AnalysisParameters {
  includeDataQuality?: boolean;
  includeRelationships?: boolean;
  includeAnomalies?: boolean;
  confidenceThreshold?: number;
  sampleSize?: number;
  customParameters?: Record<string, string | number | boolean | string[] | number[]>;
}

export interface AnalysisScope {
  dataImports?: string[];
  attributes?: string[];
  mappings?: string[];
  phases?: string[];
  fullFlow?: boolean;
}

export interface ResourceAllocation {
  cpuCores: number;
  memoryMB: number;
  estimatedCost: number;
  maxDuration: number;
}

export interface AnalysisFinding {
  id: string;
  type: string;
  category: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  description: string;
  details: Record<string, string | number | boolean | null | unknown[]>;
  evidence: Evidence[];
  confidence: number;
  impact: string;
  location?: string;
  affectedEntities?: string[];
}

export interface Evidence {
  type: 'data' | 'statistic' | 'pattern' | 'rule' | 'comparison';
  description: string;
  value?: unknown;
  source?: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface AnalysisRecommendation {
  id: string;
  findingId?: string;
  category: RecommendationCategory;
  priority: RecommendationPriority;
  title: string;
  description: string;
  rationale: string;
  steps: RecommendationStep[];
  effort: ImplementationDifficulty;
  impact: string;
  riskLevel: 'low' | 'medium' | 'high';
  dependencies?: string[];
  alternatives?: string[];
  estimatedTime?: number;
  estimatedCost?: number;
}

export interface RecommendationStep {
  order: number;
  description: string;
  automated: boolean;
  estimatedTime?: number;
  prerequisites?: string[];
  verification?: string;
}

export interface ImplementationPlan {
  totalEffort: number;
  estimatedDuration: number;
  phases: ImplementationPhase[];
  dependencies: PlanDependency[];
  risks: PlanRisk[];
  resources: RequiredResource[];
}

export interface ImplementationPhase {
  name: string;
  description: string;
  order: number;
  estimatedDuration: number;
  recommendations: string[];
  dependencies?: string[];
}

export interface PlanDependency {
  id: string;
  type: 'recommendation' | 'resource' | 'external';
  description: string;
  blocking: boolean;
}

export interface PlanRisk {
  id: string;
  level: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  mitigation: string;
  probability: number;
  impact: number;
}

export interface RequiredResource {
  type: 'human' | 'system' | 'financial' | 'time';
  description: string;
  quantity: number;
  unit: string;
  estimatedCost?: number;
}

export interface RelatedAnalysis {
  id: string;
  analysisType: AnalysisType;
  relationship: 'prerequisite' | 'complementary' | 'follow_up';
  relevanceScore: number;
}

export interface ActionableInsight {
  id: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  actionRequired: boolean;
  estimatedImpact: string;
}

export interface AnalysisTrend {
  analysisType: AnalysisType;
  period: string;
  dataPoints: TrendDataPoint[];
  trend: 'improving' | 'stable' | 'declining';
  confidence: number;
}

export interface TrendDataPoint {
  timestamp: string;
  value: number;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface AnalysisPerformanceMetrics {
  averageExecutionTime: number;
  successRate: number;
  confidenceDistribution: Record<string, number>;
  commonFindings: string[];
  improvementAreas: string[];
}

export interface AnalysisMetrics {
  executionTime: number;
  resourceUsage: ResourceUsage;
  dataVolume: DataVolume;
  qualityScores: QualityScores;
}

export interface ResourceUsage {
  cpuTime: number;
  memoryPeak: number;
  diskIO: number;
  networkIO: number;
}

export interface DataVolume {
  recordsProcessed: number;
  attributesAnalyzed: number;
  mappingsEvaluated: number;
  rulesApplied: number;
}

export interface QualityScores {
  completeness: number;
  accuracy: number;
  consistency: number;
  validity: number;
  overall: number;
}

// Enums and Types
export type AnalysisType = 'mapping_validation' | 'data_quality' | 'completeness' | 'consistency' | 'relationships' | 'anomaly_detection';
export type AnalysisStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled' | 'timeout';
export type RecommendationCategory = 'improvement' | 'optimization' | 'fix' | 'enhancement' | 'best_practice';
export type RecommendationPriority = 'critical' | 'high' | 'medium' | 'low' | 'optional';
export type ImplementationDifficulty = 'trivial' | 'easy' | 'moderate' | 'difficult' | 'complex';
