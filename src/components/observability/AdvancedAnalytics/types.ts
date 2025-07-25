/**
 * Types and Interfaces for Advanced Analytics Component
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

// Types for analytics data
export interface AnalyticsData {
  timeSeriesData: Array<{
    timestamp: string;
    [key: string]: string | number; // Dynamic agent metrics - primitive values only
  }>;
  patternAnalysis: {
    peakHours: Array<{ hour: number; activity: number }>;
    weeklyPatterns: Array<{ day: string; averagePerformance: number }>;
    seasonalTrends: Array<{ period: string; trend: 'up' | 'down' | 'stable'; magnitude: number }>;
  };
  correlationMatrix: {
    [metric1: string]: {
      [metric2: string]: number; // Correlation coefficient
    };
  };
  predictiveInsights: {
    forecasts: Array<{
      metric: string;
      predictions: Array<{ timestamp: string; value: number; confidence: number }>;
    }>;
    anomalies: Array<{
      timestamp: string;
      metric: string;
      value: number;
      expectedValue: number;
      severity: 'low' | 'medium' | 'high';
      agentName: string;
    }>;
    trends: Array<{
      metric: string;
      direction: 'improving' | 'declining' | 'stable';
      rate: number;
      significance: number;
    }>;
  };
  distributionAnalysis: Array<{
    metric: string;
    distribution: Array<{ bucket: string; count: number; percentage: number }>;
    outliers: Array<{ value: number; agentName: string; timestamp: string }>;
  }>;
}

export interface AdvancedAnalyticsProps {
  /** Agents to analyze */
  agentNames?: string[];
  /** Default time range in days */
  defaultTimeRange?: number;
  /** Show predictive analytics */
  showPredictions?: boolean;
  /** Enable data export */
  enableExport?: boolean;
  /** Refresh interval in milliseconds */
  refreshInterval?: number;
  /** CSS class name */
  className?: string;
}

export interface MetricConfig {
  key: string;
  label: string;
  color: string;
  unit: string;
  format: (value: number) => string;
}
