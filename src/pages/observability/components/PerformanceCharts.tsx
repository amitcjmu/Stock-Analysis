/**
 * PerformanceCharts Component
 * Extracted from AgentDetailPage.tsx for modularization
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { AgentMetricsChart } from '../../../components/observability';
import type { AgentDetailData, PerformanceMetrics } from '../types/AgentDetailTypes';

interface PerformanceChartsProps {
  agentData: AgentDetailData;
  performanceMetrics: PerformanceMetrics;
}

export const PerformanceCharts: React.FC<PerformanceChartsProps> = ({ agentData, performanceMetrics }) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <AgentMetricsChart 
            data={{
              data: agentData.trends.successRateHistory.map((rate, index) => ({
                timestamp: agentData.trends.timestamps[index],
                value: rate * 100,
                label: `${(rate * 100).toFixed(1)}%`
              })),
              color: '#10b981',
              trend: performanceMetrics.trend,
              changePercent: 0
            }}
            title="Success Rate Trend"
            height={200}
            showGrid
            animate
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Duration Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <AgentMetricsChart 
            data={{
              data: agentData.trends.durationHistory.map((duration, index) => ({
                timestamp: agentData.trends.timestamps[index],
                value: duration,
                label: `${duration.toFixed(1)}s`
              })),
              color: '#3b82f6',
              trend: 'stable',
              changePercent: 0
            }}
            title="Average Task Duration"
            height={200}
            showGrid
            animate
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Confidence Score Evolution</CardTitle>
        </CardHeader>
        <CardContent>
          <AgentMetricsChart 
            data={{
              data: agentData.trends.confidenceHistory.map((confidence, index) => ({
                timestamp: agentData.trends.timestamps[index],
                value: confidence * 100,
                label: `${(confidence * 100).toFixed(1)}%`
              })),
              color: '#f59e0b',
              trend: 'up',
              changePercent: 0
            }}
            title="Confidence Score Trends"
            height={200}
            showGrid
            animate
          />
        </CardContent>
      </Card>
    </div>
  );
};