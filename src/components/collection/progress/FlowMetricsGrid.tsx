/**
 * Flow Metrics Grid Component
 *
 * Displays collection flow metrics in a grid layout.
 * Extracted from Progress.tsx to create reusable metrics display.
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

export interface FlowMetrics {
  totalFlows: number;
  activeFlows: number;
  completedFlows: number;
  failedFlows: number;
  totalApplications: number;
  completedApplications: number;
  averageCompletionTime: number;
  dataQualityScore: number;
}

export interface FlowMetricsGridProps {
  metrics: FlowMetrics;
  className?: string;
}

export const FlowMetricsGrid: React.FC<FlowMetricsGridProps> = ({
  metrics,
  className = ''
}) => {
  // Type safety check for metrics prop
  if (!metrics || typeof metrics !== 'object') {
    console.warn('FlowMetricsGrid: Invalid metrics object provided');
    return (
      <div className={`p-4 border border-yellow-200 rounded-lg bg-yellow-50 ${className}`}>
        <p className="text-yellow-700 text-sm">Unable to display metrics: Invalid data provided</p>
      </div>
    );
  }

  // BUG FIX (#998): Handle both camelCase and snake_case field names from API
  // The backend returns snake_case (e.g., active_flows), but TypeScript interface uses camelCase
  //
  // ARCHITECTURAL NOTE (Per Qodo Bot Review):
  // This component-level conversion is a temporary solution. The proper fix is to implement
  // global API response transformation at the API client layer (e.g., in apiCall() utility)
  // to handle snake_case → camelCase conversion consistently across all API responses.
  // This would eliminate the need for manual conversion in every component.
  // See CLAUDE.md "API Field Naming Convention" section for migration strategy.
  const metricsAny = metrics as any;

  // Helper function to safely extract numeric metric with camelCase/snake_case fallback
  const getNumericMetric = (camelKey: keyof FlowMetrics, snakeKey: string): number => {
    const camelValue = metrics[camelKey];
    const snakeValue = metricsAny[snakeKey];

    if (typeof camelValue === 'number' && isFinite(camelValue)) {
      return camelValue;
    }
    if (typeof snakeValue === 'number' && isFinite(snakeValue)) {
      return snakeValue;
    }
    return 0;
  };

  // Safely extract and validate numeric values with fallback for both naming conventions
  const safeMetrics = {
    totalFlows: getNumericMetric('totalFlows', 'total_flows'),
    activeFlows: getNumericMetric('activeFlows', 'active_flows'),
    completedFlows: getNumericMetric('completedFlows', 'completed_flows'),
    failedFlows: getNumericMetric('failedFlows', 'failed_flows'),
    totalApplications: getNumericMetric('totalApplications', 'total_applications'),
    completedApplications: getNumericMetric('completedApplications', 'completed_applications'),
    averageCompletionTime: getNumericMetric('averageCompletionTime', 'average_completion_time'),
    dataQualityScore: getNumericMetric('dataQualityScore', 'data_quality_score'),
  };
  // Safely calculate progress percentage, avoiding NaN
  const overallProgress = safeMetrics.totalApplications > 0
    ? Math.round((safeMetrics.completedApplications / safeMetrics.totalApplications) * 100)
    : 0;

  // Safe percentage display helper with additional validation
  const safePercentageDisplay = (value: number): string => {
    if (typeof value !== 'number' || !isFinite(value) || isNaN(value)) {
      return '0';
    }
    // Ensure value is within reasonable bounds (0-100 for percentages)
    const clampedValue = Math.max(0, Math.min(100, Math.round(value)));
    return clampedValue.toString();
  };

  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`} role="region" aria-label="Flow Metrics Dashboard">
      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600" aria-label={`${safeMetrics.activeFlows} active flows`}>
              {safeMetrics.activeFlows}
            </p>
            <p className="text-sm text-muted-foreground">Active Flows</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600" aria-label={`${safeMetrics.completedApplications} applications processed`}>
              {safeMetrics.completedApplications}
            </p>
            <p className="text-sm text-muted-foreground">Apps Processed</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">{safePercentageDisplay(overallProgress)}%</p>
            <p className="text-sm text-muted-foreground">Overall Progress</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600" aria-label={`${safePercentageDisplay(safeMetrics.dataQualityScore)} percent data quality score`}>
              {safePercentageDisplay(safeMetrics.dataQualityScore)}%
            </p>
            <p className="text-sm text-muted-foreground">Data Quality</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FlowMetricsGrid;
