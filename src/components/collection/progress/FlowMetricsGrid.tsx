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

  // Safely extract and validate numeric values
  const safeMetrics = {
    totalFlows: typeof metrics.totalFlows === 'number' && isFinite(metrics.totalFlows) ? metrics.totalFlows : 0,
    activeFlows: typeof metrics.activeFlows === 'number' && isFinite(metrics.activeFlows) ? metrics.activeFlows : 0,
    completedFlows: typeof metrics.completedFlows === 'number' && isFinite(metrics.completedFlows) ? metrics.completedFlows : 0,
    failedFlows: typeof metrics.failedFlows === 'number' && isFinite(metrics.failedFlows) ? metrics.failedFlows : 0,
    totalApplications: typeof metrics.totalApplications === 'number' && isFinite(metrics.totalApplications) ? metrics.totalApplications : 0,
    completedApplications: typeof metrics.completedApplications === 'number' && isFinite(metrics.completedApplications) ? metrics.completedApplications : 0,
    averageCompletionTime: typeof metrics.averageCompletionTime === 'number' && isFinite(metrics.averageCompletionTime) ? metrics.averageCompletionTime : 0,
    dataQualityScore: typeof metrics.dataQualityScore === 'number' && isFinite(metrics.dataQualityScore) ? metrics.dataQualityScore : 0,
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
