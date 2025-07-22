/**
 * Types and Interfaces for Advanced Analytics Component
 * Part of the Agent Observability Enhancement Phase 4B - Advanced Features
 */

// Types for analytics data
export interface AnalyticsData {
  timeSeriesData: {
    timestamp: string;
    [key: string]: unknown; // Dynamic agent metrics
  }[];
  patternAnalysis: {
    peakHours: { hour: number; activity: number }[];
    weeklyPatterns: { day: string; averagePerformance: number }[];
    seasonalTrends: { period: string; trend: 'up' | 'down' | 'stable'; magnitude: number }[];
  };
  correlationMatrix: {
    [metric1: string]: {
      [metric2: string]: number; // Correlation coefficient
    };
  };
  predictiveInsights: {
    forecasts: {
      metric: string;
      predictions: { timestamp: string; value: number; confidence: number }[];
    }[];
    anomalies: {
      timestamp: string;
      metric: string;
      value: number;
      expectedValue: number;
      severity: 'low' | 'medium' | 'high';
      agentName: string;
    }[];
    trends: {
      metric: string;
      direction: 'improving' | 'declining' | 'stable';
      rate: number;
      significance: number;
    }[];
  };
  distributionAnalysis: {
    metric: string;
    distribution: { bucket: string; count: number; percentage: number }[];
    outliers: { value: number; agentName: string; timestamp: string }[];
  }[];
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