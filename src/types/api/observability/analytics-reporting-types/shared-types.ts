/**
 * Shared Supporting Types
 * 
 * Common type definitions used across multiple analytics and reporting modules.
 * These types are shared to avoid duplication and maintain consistency.
 */

// Common Impact and Measurement Types
export interface ImpactMeasure {
  current: number;
  projected: number;
  improvement: number;
  confidence: number;
  unit: string;
}

export interface BenefitMeasure {
  quantified: boolean;
  value: number;
  unit: string;
  description: string;
  confidence: number;
}

// Business and Technical Impact Types
export interface BusinessImpact {
  revenue: number;
  customers: number;
  reputation: 'minimal' | 'moderate' | 'significant' | 'severe';
  compliance: boolean;
}

export interface TechnicalImpact {
  performance: number;
  availability: number;
  security: 'low' | 'medium' | 'high' | 'critical';
  scalability: 'minimal' | 'moderate' | 'significant' | 'severe';
}

// Evidence and Analysis Types
export interface CauseEvidence {
  type: 'metric' | 'log' | 'trace' | 'event';
  source: string;
  evidence: string;
  weight: number;
  timestamp: string;
}

// Baseline and Condition Types
export interface BaselineMetric {
  name: string;
  value: number;
  unit: string;
  confidence: number;
  conditions: string[];
}

export interface BaselineCondition {
  parameter: string;
  value: unknown;
  tolerance: number;
  critical: boolean;
}

// Usage and Capacity Types
export interface UsageFactor {
  name: string;
  impact: number;
  confidence: number;
  type: 'business' | 'technical' | 'seasonal';
}

export interface ProjectedUsage {
  period: string;
  usage: number;
  confidence: number;
  factors: UsageFactor[];
}

export interface RequiredCapacity {
  period: string;
  capacity: number;
  buffer: number;
  reasoning: string;
}

export interface UtilizationForecast {
  period: string;
  utilization: number;
  status: 'healthy' | 'warning' | 'critical';
  threshold: number;
}

export interface BottleneckPrediction {
  period: string;
  probability: number;
  type: 'capacity' | 'performance' | 'throughput';
  severity: 'low' | 'medium' | 'high';
}

// Metrics Analysis Types
export interface MetricValue {
  timestamp: string;
  value: number;
  quality: 'high' | 'medium' | 'low';
}

export interface MetricStatistics {
  count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
  p95: number;
  p99: number;
  stdDev: number;
}

export interface MetricTrend {
  direction: 'increasing' | 'decreasing' | 'stable' | 'volatile';
  rate: number;
  confidence: number;
  significance: 'low' | 'medium' | 'high';
}

export interface MetricAnomaly {
  timestamp: string;
  value: number;
  expected: number;
  deviation: number;
  type: 'spike' | 'dip' | 'drift';
  confidence: number;
}

export interface ThresholdAnalysis {
  breaches: number;
  nearMisses: number;
  worstBreach: number;
  averageBreach: number;
  breachDuration: string;
}

// Trend and Seasonality Types
export interface TrendData {
  timestamp: string;
  value: number;
  trend: 'up' | 'down' | 'stable';
}

export interface SeasonalPattern {
  pattern: 'daily' | 'weekly' | 'monthly' | 'yearly';
  amplitude: number;
  phase: number;
  confidence: number;
}

// Correlation and Causality Types
export interface CausalityAnalysis {
  causal: boolean;
  direction: 'x_causes_y' | 'y_causes_x' | 'bidirectional' | 'spurious';
  confidence: number;
  lagTime: string;
  strength: 'weak' | 'moderate' | 'strong';
}

// Prediction Types
export interface PredictionFactor {
  name: string;
  weight: number;
  direction: 'positive' | 'negative' | 'neutral';
  confidence: number;
}