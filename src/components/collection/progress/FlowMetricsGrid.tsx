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
  const metricsAny = metrics as any;

  // Safely extract and validate numeric values with fallback for both naming conventions
  const safeMetrics = {
    totalFlows: typeof metrics.totalFlows === 'number' && isFinite(metrics.totalFlows) ? metrics.totalFlows :
                (typeof metricsAny.total_flows === 'number' && isFinite(metricsAny.total_flows) ? metricsAny.total_flows : 0),
    activeFlows: typeof metrics.activeFlows === 'number' && isFinite(metrics.activeFlows) ? metrics.activeFlows :
                 (typeof metricsAny.active_flows === 'number' && isFinite(metricsAny.active_flows) ? metricsAny.active_flows : 0),
    completedFlows: typeof metrics.completedFlows === 'number' && isFinite(metrics.completedFlows) ? metrics.completedFlows :
                    (typeof metricsAny.completed_flows === 'number' && isFinite(metricsAny.completed_flows) ? metricsAny.completed_flows : 0),
    failedFlows: typeof metrics.failedFlows === 'number' && isFinite(metrics.failedFlows) ? metrics.failedFlows :
                 (typeof metricsAny.failed_flows === 'number' && isFinite(metricsAny.failed_flows) ? metricsAny.failed_flows : 0),
    totalApplications: typeof metrics.totalApplications === 'number' && isFinite(metrics.totalApplications) ? metrics.totalApplications :
                       (typeof metricsAny.total_applications === 'number' && isFinite(metricsAny.total_applications) ? metricsAny.total_applications : 0),
    completedApplications: typeof metrics.completedApplications === 'number' && isFinite(metrics.completedApplications) ? metrics.completedApplications :
                           (typeof metricsAny.completed_applications === 'number' && isFinite(metricsAny.completed_applications) ? metricsAny.completed_applications : 0),
    averageCompletionTime: typeof metrics.averageCompletionTime === 'number' && isFinite(metrics.averageCompletionTime) ? metrics.averageCompletionTime :
                           (typeof metricsAny.average_completion_time === 'number' && isFinite(metricsAny.average_completion_time) ? metricsAny.average_completion_time : 0),
    dataQualityScore: typeof metrics.dataQualityScore === 'number' && isFinite(metrics.dataQualityScore) ? metrics.dataQualityScore :
                      (typeof metricsAny.data_quality_score === 'number' && isFinite(metricsAny.data_quality_score) ? metricsAny.data_quality_score : 0),
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
