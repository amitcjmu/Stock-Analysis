/**
 * Capacity Planning Types
 * 
 * Type definitions for capacity analysis, growth projections, resource planning,
 * and generating capacity recommendations and risk assessments.
 */

import {
  CreateRequest,
  CreateResponse,
  MultiTenantContext
} from '../../shared';
import {
  ProjectedUsage,
  RequiredCapacity,
  UtilizationForecast,
  BottleneckPrediction,
  UsageFactor
} from './shared-types';

// Capacity Planning Requests and Responses
export interface CreateCapacityPlanRequest extends CreateRequest<CapacityPlanData> {
  flowId: string;
  data: CapacityPlanData;
  planningHorizon: 'week' | 'month' | 'quarter' | 'year';
  growthProjections: GrowthProjection[];
  constraints: CapacityConstraint[];
  scenarios: CapacityScenario[];
  includeRecommendations?: boolean;
}

export interface CreateCapacityPlanResponse extends CreateResponse<CapacityPlan> {
  data: CapacityPlan;
  planId: string;
  projections: CapacityProjection[];
  recommendations: CapacityRecommendation[];
  riskAssessment: CapacityRisk[];
}

// Core Capacity Planning Types
export interface CapacityPlanData {
  name: string;
  description?: string;
  horizon: 'week' | 'month' | 'quarter' | 'year';
  baselineDate: string;
  resources: ResourceType[];
  objectives: CapacityObjective[];
  assumptions: PlanningAssumption[];
  metadata: Record<string, any>;
}

export interface GrowthProjection {
  resource: string;
  currentCapacity: number;
  projectedGrowthRate: number;
  seasonality: SeasonalityPattern[];
  businessDrivers: BusinessDriver[];
  confidence: number;
}

export interface CapacityConstraint {
  id: string;
  type: 'budget' | 'technical' | 'operational' | 'regulatory' | 'business';
  description: string;
  impact: ConstraintImpact;
  workarounds: string[];
  timeline: string;
}

export interface CapacityScenario {
  id: string;
  name: string;
  description: string;
  probability: number;
  growthMultiplier: number;
  assumptions: ScenarioAssumption[];
  impact: ScenarioImpact;
}

export interface CapacityPlan {
  id: string;
  planId: string;
  name: string;
  description?: string;
  flowId: string;
  horizon: 'week' | 'month' | 'quarter' | 'year';
  baselineDate: string;
  status: 'draft' | 'active' | 'archived' | 'superseded';
  summary: CapacityPlanSummary;
  projections: CapacityProjection[];
  recommendations: CapacityRecommendation[];
  scenarios: CapacityScenarioResult[];
  riskAssessment: CapacityRisk[];
  createdAt: string;
  updatedAt: string;
}

export interface CapacityProjection {
  resource: string;
  currentUsage: number;
  currentCapacity: number;
  projectedUsage: ProjectedUsage[];
  requiredCapacity: RequiredCapacity[];
  utilizationForecast: UtilizationForecast[];
  bottleneckPrediction: BottleneckPrediction[];
}

export interface CapacityRecommendation {
  id: string;
  type: 'scaling' | 'optimization' | 'migration' | 'procurement' | 'architectural';
  priority: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  resource: string;
  timeline: string;
  cost: RecommendationCost;
  benefits: RecommendationBenefit[];
  risks: CapacityRecommendationRisk[];
  dependencies: string[];
}

export interface CapacityRisk {
  id: string;
  type: 'capacity_shortage' | 'over_provisioning' | 'budget_overrun' | 'technical_debt' | 'vendor_dependency';
  severity: 'low' | 'medium' | 'high' | 'critical';
  probability: number;
  impact: RiskImpact;
  timeframe: string;
  mitigation: RiskMitigation[];
  indicators: RiskIndicator[];
}

// Supporting Capacity Types
export interface ResourceType {
  name: string;
  type: 'compute' | 'storage' | 'network' | 'database' | 'application';
  unit: string;
  cost: number;
  scalability: 'manual' | 'automatic' | 'elastic';
}

export interface CapacityObjective {
  id: string;
  metric: string;
  target: number;
  threshold: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

export interface PlanningAssumption {
  id: string;
  type: 'growth' | 'technology' | 'business' | 'external';
  description: string;
  confidence: number;
  impact: string;
}

export interface SeasonalityPattern {
  pattern: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  multiplier: number;
  confidence: number;
  description: string;
}

export interface BusinessDriver {
  name: string;
  type: 'user_growth' | 'feature_release' | 'marketing_campaign' | 'seasonal';
  impact: number;
  timeframe: string;
  confidence: number;
}

export interface ConstraintImpact {
  type: 'blocking' | 'limiting' | 'delaying' | 'increasing_cost';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  affectedResources: string[];
}

export interface ScenarioAssumption {
  id: string;
  description: string;
  parameter: string;
  value: any;
  confidence: number;
}

export interface ScenarioImpact {
  resources: Record<string, number>;
  timeline: string;
  cost: number;
  risk: 'low' | 'medium' | 'high';
}

export interface CapacityPlanSummary {
  totalResources: number;
  projectedGrowth: number;
  recommendedActions: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  budgetImpact: number;
}

export interface CapacityScenarioResult {
  scenarioId: string;
  name: string;
  probability: number;
  projections: CapacityProjection[];
  recommendations: string[];
  risk: 'low' | 'medium' | 'high';
}


export interface RecommendationCost {
  implementation: number;
  operational: number;
  maintenance: number;
  total: number;
  currency: string;
  timeframe: string;
}

export interface RecommendationBenefit {
  type: 'cost_savings' | 'performance_improvement' | 'risk_reduction' | 'efficiency_gain';
  description: string;
  quantified: boolean;
  value: number;
  unit: string;
  timeframe: string;
}

export interface CapacityRecommendationRisk {
  type: 'implementation' | 'operational' | 'financial' | 'technical';
  description: string;
  probability: number;
  impact: 'low' | 'medium' | 'high';
  mitigation: string[];
}

export interface RiskImpact {
  operational: 'low' | 'medium' | 'high' | 'critical';
  financial: number;
  reputation: 'minimal' | 'moderate' | 'significant' | 'severe';
  compliance: boolean;
  timeframe: string;
}

export interface RiskMitigation {
  id: string;
  strategy: 'avoid' | 'reduce' | 'transfer' | 'accept';
  actions: string[];
  cost: number;
  effectiveness: number;
  timeline: string;
}

export interface RiskIndicator {
  metric: string;
  threshold: number;
  current: number;
  trend: 'improving' | 'degrading' | 'stable';
  alerting: boolean;
}

