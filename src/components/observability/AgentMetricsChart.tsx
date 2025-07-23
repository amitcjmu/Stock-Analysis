/**
 * Agent Metrics Chart Component
 * Visualization components for agent performance trends and metrics
 * Part of the Agent Observability Enhancement Phase 4A
 */

import React from 'react'
import { useMemo } from 'react'
import { cn } from '../../lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Zap } from 'lucide-react'
import { TrendingUp, TrendingDown, Activity, BarChart3, Target, Timer } from 'lucide-react'
import type { 
  MetricsChartProps, 
  SparklineData, 
  ChartDataPoint,
  AgentMetricsData 
} from '../../types/api/observability/agent-performance';

// Helper function to calculate trend
const calculateTrend = (data: number[]): { direction: 'up' | 'down' | 'stable'; percentage: number } => {
  if (data.length < 2) return { direction: 'stable', percentage: 0 };
  
  const start = data[0];
  const end = data[data.length - 1];
  const percentage = start !== 0 ? ((end - start) / start) * 100 : 0;
  
  if (Math.abs(percentage) < 1) return { direction: 'stable', percentage: 0 };
  return { 
    direction: percentage > 0 ? 'up' : 'down', 
    percentage: Math.abs(percentage) 
  };
};

// Sparkline Chart Component
export const SparklineChart: React.FC<MetricsChartProps> = ({
  data,
  title,
  height = 60,
  showGrid = false,
  animate = true,
  className
}) => {
  const { points, maxValue, minValue } = useMemo(() => {
    const values = data.data.map(d => d.value);
    const max = Math.max(...values);
    const min = Math.min(...values);
    
    const points = data.data.map((point, index) => {
      const x = (index / (data.data.length - 1)) * 100;
      const y = max !== min ? ((max - point.value) / (max - min)) * 100 : 50;
      return `${x},${y}`;
    }).join(' ');
    
    return { points, maxValue: max, minValue: min };
  }, [data.data]);

  const trend = calculateTrend(data.data.map(d => d.value));
  
  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">{title}</h4>
        <div className="flex items-center space-x-1">
          {trend.direction === 'up' && <TrendingUp className="h-3 w-3 text-green-500" />}
          {trend.direction === 'down' && <TrendingDown className="h-3 w-3 text-red-500" />}
          {trend.percentage > 0 && (
            <span className={cn(
              'text-xs font-medium',
              trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
            )}>
              {trend.percentage.toFixed(1)}%
            </span>
          )}
        </div>
      </div>
      
      <div className="relative" style={{ height }}>
        <svg 
          width="100%" 
          height="100%" 
          className="absolute inset-0"
          preserveAspectRatio="none"
        >
          {showGrid && (
            <g className="opacity-20">
              <line x1="0" y1="25%" x2="100%" y2="25%" stroke="currentColor" strokeWidth="0.5" />
              <line x1="0" y1="50%" x2="100%" y2="50%" stroke="currentColor" strokeWidth="0.5" />
              <line x1="0" y1="75%" x2="100%" y2="75%" stroke="currentColor" strokeWidth="0.5" />
            </g>
          )}
          
          <polyline
            fill="none"
            stroke={data.color}
            strokeWidth="2"
            points={points}
            className={animate ? 'transition-all duration-1000 ease-in-out' : ''}
          />
          
          {/* Data points */}
          {data.data.map((point, index) => {
            const x = (index / (data.data.length - 1)) * 100;
            const y = maxValue !== minValue ? ((maxValue - point.value) / (maxValue - minValue)) * 100 : 50;
            return (
              <circle
                key={index}
                cx={`${x}%`}
                cy={`${y}%`}
                r="2"
                fill={data.color}
                className="opacity-70 hover:opacity-100 transition-opacity"
              >
                <title>{`${point.label || point.timestamp}: ${point.value}`}</title>
              </circle>
            );
          })}
        </svg>
      </div>
      
      <div className="flex justify-between text-xs text-gray-500">
        <span>{minValue.toFixed(1)}</span>
        <span>{maxValue.toFixed(1)}</span>
      </div>
    </div>
  );
};

// Performance Distribution Chart (Simple Bar Chart)
export const PerformanceDistributionChart: React.FC<{
  data: { label: string; value: number; color: string }[];
  title: string;
  className?: string;
}> = ({ data, title, className }) => {
  const maxValue = Math.max(...data.map(d => d.value));
  
  return (
    <div className={cn('space-y-3', className)}>
      <h4 className="text-sm font-medium text-gray-700">{title}</h4>
      <div className="space-y-2">
        {data.map((item, index) => (
          <div key={index} className="space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-600">{item.label}</span>
              <span className="text-xs font-medium">{item.value}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all duration-500"
                style={{
                  backgroundColor: item.color,
                  width: `${(item.value / maxValue) * 100}%`
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Success Rate Gauge Component
export const SuccessRateGauge: React.FC<{
  value: number;
  size?: number;
  className?: string;
}> = ({ value, size = 80, className }) => {
  const percentage = value * 100;
  const angle = (percentage / 100) * 180;
  const color = percentage >= 90 ? '#10b981' : percentage >= 70 ? '#f59e0b' : '#ef4444';
  
  return (
    <div className={cn('flex flex-col items-center space-y-2', className)}>
      <div className="relative" style={{ width: size, height: size / 2 }}>
        <svg width={size} height={size / 2} className="transform rotate-180">
          {/* Background arc */}
          <path
            d={`M 10 ${size / 2 - 10} A ${size / 2 - 10} ${size / 2 - 10} 0 0 1 ${size - 10} ${size / 2 - 10}`}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="8"
            strokeLinecap="round"
          />
          {/* Progress arc */}
          <path
            d={`M 10 ${size / 2 - 10} A ${size / 2 - 10} ${size / 2 - 10} 0 0 1 ${size - 10} ${size / 2 - 10}`}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(angle / 180) * Math.PI * (size / 2 - 10)} ${Math.PI * (size / 2 - 10)}`}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-end justify-center pb-2">
          <span className="text-lg font-bold" style={{ color }}>
            {percentage.toFixed(1)}%
          </span>
        </div>
      </div>
      <span className="text-xs text-gray-600">Success Rate</span>
    </div>
  );
};

// Comprehensive Metrics Dashboard
export const AgentMetricsDashboard: React.FC<{
  agentData: AgentMetricsData;
  className?: string;
}> = ({ agentData, className }) => {
  const successRateData: SparklineData = {
    data: agentData.trends.successRateHistory.map((value, index) => ({
      timestamp: agentData.trends.timestamps[index] || `T${index}`,
      value
    })),
    color: '#3b82f6',
    trend: calculateTrend(agentData.trends.successRateHistory).direction,
    changePercent: calculateTrend(agentData.trends.successRateHistory).percentage
  };
  
  const durationData: SparklineData = {
    data: agentData.trends.durationHistory.map((value, index) => ({
      timestamp: agentData.trends.timestamps[index] || `T${index}`,
      value
    })),
    color: '#8b5cf6',
    trend: calculateTrend(agentData.trends.durationHistory).direction,
    changePercent: calculateTrend(agentData.trends.durationHistory).percentage
  };
  
  const taskCountData: SparklineData = {
    data: agentData.trends.taskCountHistory.map((value, index) => ({
      timestamp: agentData.trends.timestamps[index] || `T${index}`,
      value
    })),
    color: '#10b981',
    trend: calculateTrend(agentData.trends.taskCountHistory).direction,
    changePercent: calculateTrend(agentData.trends.taskCountHistory).percentage
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header with agent name and status */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{agentData.agentName} Metrics</h3>
        <Badge variant={agentData.status.isHealthy ? "default" : "destructive"}>
          {agentData.status.current}
        </Badge>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Target className="h-4 w-4 text-blue-500" />
              <span>Success Rate</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SuccessRateGauge value={agentData.metrics.successRate} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Timer className="h-4 w-4 text-purple-500" />
              <span>Avg Duration</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-2">
              <div className="text-2xl font-bold text-gray-900">
                {agentData.metrics.avgDuration.toFixed(1)}s
              </div>
              <div className="text-sm text-gray-500">Per Task</div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <Activity className="h-4 w-4 text-green-500" />
              <span>Total Tasks</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center space-y-2">
              <div className="text-2xl font-bold text-gray-900">
                {agentData.metrics.totalTasks}
              </div>
              <div className="text-sm text-gray-500">
                {agentData.metrics.completedTasks} completed
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trend Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <SparklineChart
              data={successRateData}
              title="Success Rate Trend"
              height={80}
              animate={true}
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <SparklineChart
              data={durationData}
              title="Duration Trend"
              height={80}
              animate={true}
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <SparklineChart
              data={taskCountData}
              title="Task Volume Trend"
              height={80}
              animate={true}
            />
          </CardContent>
        </Card>
      </div>

      {/* Performance Distribution */}
      {agentData.metrics.memoryUsage && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium flex items-center space-x-2">
              <BarChart3 className="h-4 w-4 text-orange-500" />
              <span>Resource Usage</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <PerformanceDistributionChart
              title="Memory & LLM Usage"
              data={[
                {
                  label: 'Memory Usage (MB)',
                  value: agentData.metrics.memoryUsage,
                  color: '#f59e0b'
                },
                {
                  label: 'LLM Calls',
                  value: agentData.metrics.llmCalls,
                  color: '#3b82f6'
                },
                {
                  label: 'Confidence Score',
                  value: agentData.metrics.confidence * 100,
                  color: '#10b981'
                }
              ]}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AgentMetricsDashboard;