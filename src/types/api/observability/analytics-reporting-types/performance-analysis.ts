/**
 * Performance Analysis Types
 * 
 * Type definitions for analyzing performance metrics, identifying bottlenecks,
 * generating recommendations, and tracking performance trends.
 */

import {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext
} from '../../shared';
import {
  ImpactMeasure,
  BenefitMeasure,
  BusinessImpact,
  TechnicalImpact,
  CauseEvidence,
  BaselineMetric,
  BaselineCondition,
  MetricValue,
  MetricStatistics,
  MetricTrend,
  MetricAnomaly,
  ThresholdAnalysis,
  CausalityAnalysis
} from './shared-types';

// Performance Analysis Requests and Responses
export interface AnalyzePerformanceRequest extends BaseApiRequest {
  flowId: string;
  analysisType: 'latency' | 'throughput' | 'errors' | 'capacity' | 'bottlenecks';
  timeRange: {
    start: string;
    end: string;
  };
  scope: PerformanceScope;
  metrics: PerformanceMetric[];
  thresholds: PerformanceThreshold[];
  context: MultiTenantContext;
}

export interface AnalyzePerformanceResponse extends BaseApiResponse<PerformanceAnalysis> {
  data: PerformanceAnalysis;
  analysisId: string;
  findings: PerformanceFinding[];
  recommendations: PerformanceRecommendation[];
  bottlenecks: PerformanceBottleneck[];
  trends: PerformanceTrend[];
}

// Core Performance Types
export interface PerformanceScope {
  services: string[];
  environments: string[];
  regions: string[];
  userSegments: string[];
  businessProcesses: string[];
  timeZones: string[];
}

export interface PerformanceMetric {
  name: string;
  type: 'latency' | 'throughput' | 'error_rate' | 'availability' | 'utilization';
  aggregation: 'avg' | 'p50' | 'p95' | 'p99' | 'max' | 'min' | 'sum';
  unit: string;
  target?: number;
  threshold?: number;
}

export interface PerformanceThreshold {
  metric: string;
  warning: number;
  critical: number;
  unit: string;
  operator: 'gt' | 'gte' | 'lt' | 'lte';
}

export interface PerformanceAnalysis {
  id: string;
  analysisType: 'latency' | 'throughput' | 'errors' | 'capacity' | 'bottlenecks';
  timeRange: {
    start: string;
    end: string;
  };
  scope: PerformanceScope;
  summary: PerformanceAnalysisSummary;
  metrics: AnalyzedMetric[];
  correlations: PerformanceCorrelation[];
  patterns: PerformancePattern[];
  baseline: PerformanceBaseline;
  createdAt: string;
}

export interface PerformanceFinding {
  id: string;
  type: 'bottleneck' | 'anomaly' | 'trend' | 'threshold_breach' | 'correlation';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  impact: FindingImpact;
  evidence: FindingEvidence[];
  affectedComponents: string[];
  timeframe: string;
  confidence: number;
}

export interface PerformanceRecommendation {
  id: string;
  type: 'optimization' | 'scaling' | 'configuration' | 'architecture' | 'monitoring';
  title: string;
  description: string;
  rationale: string;
  impact: RecommendationImpact;
  effort: 'low' | 'medium' | 'high';
  priority: number;
  implementationSteps: ImplementationStep[];
  estimatedBenefit: EstimatedBenefit;
  risks: RecommendationRisk[];
}

export interface PerformanceBottleneck {
  id: string;
  component: string;
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'database' | 'application' | 'external';
  severity: 'low' | 'medium' | 'high' | 'critical';
  metric: string;
  currentValue: number;
  threshold: number;
  impact: BottleneckImpact;
  duration: string;
  frequency: 'rare' | 'occasional' | 'frequent' | 'constant';
  rootCause: RootCauseAnalysis;
}

export interface PerformanceTrend {
  metric: string;
  direction: 'improving' | 'degrading' | 'stable' | 'volatile';
  rate: number;
  confidence: number;
  timeframe: string;
  seasonality: SeasonalityInfo;
  forecast: TrendForecast;
  significance: 'low' | 'medium' | 'high';
}

// Supporting Performance Types
export interface PerformanceAnalysisSummary {
  overallScore: number;
  criticalIssues: number;
  optimizationOpportunities: number;
  baseline: PerformanceBaseline;
  keyFindings: string[];
}

export interface AnalyzedMetric {
  name: string;
  values: MetricValue[];
  statistics: MetricStatistics;
  thresholds: ThresholdAnalysis;
  trends: MetricTrend;
  anomalies: MetricAnomaly[];
}

export interface PerformanceCorrelation {
  metrics: string[];
  coefficient: number;
  pValue: number;
  strength: 'weak' | 'moderate' | 'strong';
  significance: boolean;
  causality: CausalityAnalysis;
}

export interface PerformancePattern {
  id: string;
  type: 'periodic' | 'trending' | 'threshold' | 'burst' | 'gradual';
  description: string;
  metrics: string[];
  frequency: string;
  confidence: number;
  firstObserved: string;
  lastObserved: string;
}

export interface PerformanceBaseline {
  period: string;
  metrics: BaselineMetric[];
  conditions: BaselineCondition[];
  confidence: number;
  validFrom: string;
  validTo: string;
}

export interface FindingImpact {
  scope: 'service' | 'system' | 'business' | 'user';
  severity: 'low' | 'medium' | 'high' | 'critical';
  affectedUsers: number;
  businessImpact: BusinessImpact;
  technicalImpact: TechnicalImpact;
}

export interface FindingEvidence {
  type: 'metric' | 'log' | 'trace' | 'event' | 'alert';
  source: string;
  value: any;
  timestamp: string;
  confidence: number;
}

export interface RecommendationImpact {
  performance: ImpactMeasure;
  availability: ImpactMeasure;
  cost: ImpactMeasure;
  complexity: ImpactMeasure;
  risk: ImpactMeasure;
}

export interface ImplementationStep {
  order: number;
  title: string;
  description: string;
  estimatedTime: string;
  resources: string[];
  dependencies: string[];
  risks: string[];
}

export interface EstimatedBenefit {
  performance: BenefitMeasure;
  availability: BenefitMeasure;
  cost: BenefitMeasure;
  timeframe: string;
  confidence: number;
}

export interface RecommendationRisk {
  type: 'implementation' | 'operational' | 'business' | 'technical';
  description: string;
  probability: number;
  impact: 'low' | 'medium' | 'high';
  mitigation: string[];
}

export interface BottleneckImpact {
  responseTime: number;
  throughput: number;
  userExperience: 'minimal' | 'moderate' | 'significant' | 'severe';
  businessImpact: 'low' | 'medium' | 'high' | 'critical';
  cascadeEffects: string[];
}

export interface RootCauseAnalysis {
  primaryCause: string;
  contributingFactors: string[];
  evidence: CauseEvidence[];
  confidence: number;
  investigationMethod: string;
}

export interface SeasonalityInfo {
  detected: boolean;
  period: string;
  strength: number;
  peaks: string[];
  valleys: string[];
}

export interface TrendForecast {
  nextPeriod: number;
  confidence: number;
  upperBound: number;
  lowerBound: number;
  assumptions: string[];
}

