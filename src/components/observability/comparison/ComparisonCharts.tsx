/**
 * Comparison charts components extracted from AgentComparison
 * Includes trend charts and radar charts for agent comparison
 */

import React from 'react'
import { useMemo } from 'react'
import { BarChart, Bar } from 'recharts'
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { AgentComparisonData } from '../hooks/useAgentComparison';
import { COMPARISON_METRICS } from '../utils/constants';

interface ComparisonChartsProps {
  comparisonData: AgentComparisonData[];
}

interface TrendChartDataPoint {
  index: number;
  timestamp?: string;
  [key: string]: number | string | undefined;
}

interface RadarChartDataPoint {
  metric: string;
  [key: string]: string | number;
}

export const SuccessRateTrendChart: React.FC<ComparisonChartsProps> = ({ comparisonData }) => {
  const chartData = useMemo(() => {
    if (comparisonData.length === 0) return [];

    const maxLength = Math.max(...comparisonData.map(agent => agent.trends.timestamps.length));
    
    return Array.from({ length: maxLength }, (_, index) => {
      const dataPoint: TrendChartDataPoint = { index };
      
      comparisonData.forEach(agent => {
        if (agent.trends.timestamps[index]) {
          dataPoint[`${agent.agentName}_success`] = agent.trends.successRateHistory[index] * 100;
          dataPoint.timestamp = agent.trends.timestamps[index];
        }
      });
      
      return dataPoint;
    });
  }, [comparisonData]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Success Rate Trends</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="index" />
            <YAxis />
            <Tooltip />
            <Legend />
            {comparisonData.map((agent, index) => (
              <Line
                key={agent.agentName}
                type="monotone"
                dataKey={`${agent.agentName}_success`}
                stroke={`hsl(${index * 120}, 70%, 50%)`}
                strokeWidth={2}
                name={agent.agentName}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export const PerformanceRadarChart: React.FC<ComparisonChartsProps> = ({ comparisonData }) => {
  const radarData = useMemo(() => {
    return COMPARISON_METRICS.slice(0, 6).map(metric => {
      const dataPoint: RadarChartDataPoint = { metric: metric.label };
      
      comparisonData.forEach(agent => {
        const value = agent.metrics[metric.key];
        // Normalize values to 0-100 scale for radar chart
        let normalizedValue;
        if (metric.key === 'successRate' || metric.key === 'avgConfidence') {
          normalizedValue = value * 100;
        } else if (metric.key === 'avgDuration') {
          normalizedValue = Math.max(0, 100 - (value / 10) * 100); // Invert duration
        } else if (metric.key === 'errorRate') {
          normalizedValue = Math.max(0, 100 - (value * 100)); // Invert error rate
        } else {
          normalizedValue = Math.min(100, (value / 100) * 100); // Scale other metrics
        }
        
        dataPoint[agent.agentName] = normalizedValue;
      });
      
      return dataPoint;
    });
  }, [comparisonData]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Performance Radar</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="metric" />
            <PolarRadiusAxis angle={90} domain={[0, 100]} />
            {comparisonData.map((agent, index) => (
              <Radar
                key={agent.agentName}
                name={agent.agentName}
                dataKey={agent.agentName}
                stroke={`hsl(${index * 120}, 70%, 50%)`}
                fill={`hsl(${index * 120}, 70%, 50%)`}
                fillOpacity={0.2}
              />
            ))}
            <Legend />
          </RadarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};