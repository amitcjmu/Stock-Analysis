/**
 * Trends Tab Component
 * Displays time series charts and metric selection
 */

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../ui/card';
import { Button } from '../../../ui/button';
import { METRIC_CONFIGS } from '../constants';

interface TrendsTabProps {
  chartData: Array<Record<string, string | number>>;
  agentNames: string[];
  selectedMetrics: string[];
  onMetricToggle: (metric: string) => void;
}

const TrendsTab: React.FC<TrendsTabProps> = ({
  chartData,
  agentNames,
  selectedMetrics,
  onMetricToggle
}) => {
  return (
    <div className="space-y-6">
      {/* Metric Selection */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Select Metrics to Display</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {METRIC_CONFIGS.map(metric => (
              <Button
                key={metric.key}
                variant={selectedMetrics.includes(metric.key) ? "default" : "outline"}
                size="sm"
                onClick={() => onMetricToggle(metric.key)}
              >
                <div 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: metric.color }}
                />
                {metric.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Time Series Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Trends Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              {agentNames.map((agent, agentIndex) =>
                selectedMetrics.map((metric, metricIndex) => {
                  const config = METRIC_CONFIGS.find(m => m.key === metric);
                  return (
                    <Line
                      key={`${agent}_${metric}`}
                      type="monotone"
                      dataKey={`${agent}_${metric}`}
                      stroke={config?.color || `hsl(${(agentIndex * 60 + metricIndex * 120) % 360}, 70%, 50%)`}
                      strokeWidth={2}
                      name={`${agent} ${config?.label || metric}`}
                    />
                  );
                })
              )}
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
};

export default TrendsTab;