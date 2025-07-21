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
  const overallProgress = Math.round((metrics.completedApplications / metrics.totalApplications) * 100);

  return (
    <div className={`grid grid-cols-1 md:grid-cols-4 gap-4 ${className}`}>
      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">{metrics.activeFlows}</p>
            <p className="text-sm text-muted-foreground">Active Flows</p>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{metrics.completedApplications}</p>
            <p className="text-sm text-muted-foreground">Apps Processed</p>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">{overallProgress}%</p>
            <p className="text-sm text-muted-foreground">Overall Progress</p>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600">{metrics.dataQualityScore}%</p>
            <p className="text-sm text-muted-foreground">Data Quality</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FlowMetricsGrid;