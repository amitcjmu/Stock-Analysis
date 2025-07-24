import React from 'react';
import { 
  Activity, 
  Users, 
  Target, 
  TrendingUp,
  Database,
  Network,
  MessageSquare,
  Lightbulb
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { SystemMetrics } from '../types';
import type { FlowMetrics } from '../hooks/useFlowMetrics';

interface MetricsPanelProps {
  systemMetrics: SystemMetrics | null;
  flowMetrics: FlowMetrics;
}

export const MetricsPanel: React.FC<MetricsPanelProps> = ({
  systemMetrics,
  flowMetrics
}) => {
  if (!systemMetrics) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-center">
            <Activity className="h-8 w-8 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Loading system metrics...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const memoryUsagePercentage = (systemMetrics.memory_utilization_gb / systemMetrics.total_memory_gb) * 100;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">System Metrics</h2>
      
      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Flows</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.total_active_flows}</div>
            <p className="text-xs text-gray-600">
              {flowMetrics.runningFlows} running, {flowMetrics.completedFlows} completed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.total_agents}</div>
            <p className="text-xs text-gray-600">
              Across {systemMetrics.total_active_flows} flows
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <Target className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(systemMetrics.success_rate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-600">
              Last 30 days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Completion</CardTitle>
            <TrendingUp className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {systemMetrics.avg_completion_time_hours.toFixed(1)}h
            </div>
            <p className="text-xs text-gray-600">
              Per flow
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Memory Usage */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Database className="h-5 w-5 text-blue-600" />
              <span>Memory Utilization</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Memory Usage</span>
                <span className="font-medium">
                  {systemMetrics.memory_utilization_gb.toFixed(1)} GB / {systemMetrics.total_memory_gb.toFixed(1)} GB
                </span>
              </div>
              <Progress value={memoryUsagePercentage} className="h-2" />
              <p className="text-xs text-gray-600">
                {memoryUsagePercentage.toFixed(1)}% of total system memory
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Knowledge Bases */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Lightbulb className="h-5 w-5 text-yellow-600" />
              <span>Knowledge Bases</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-2xl font-bold">
              {systemMetrics.knowledge_bases_loaded}
            </div>
            <p className="text-sm text-gray-600">
              Knowledge bases loaded and ready for agent collaboration
            </p>
            <div className="text-xs text-gray-500">
              Including migration patterns, best practices, and domain expertise
            </div>
          </CardContent>
        </Card>

        {/* Collaboration Events */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5 text-green-600" />
              <span>Collaboration Events</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-2xl font-bold">
              {systemMetrics.collaboration_events_today.toLocaleString()}
            </div>
            <p className="text-sm text-gray-600">
              Inter-agent communications today
            </p>
            <div className="text-xs text-gray-500">
              Includes crew handoffs, knowledge sharing, and validation requests
            </div>
          </CardContent>
        </Card>

        {/* Flow Phases */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Network className="h-5 w-5 text-purple-600" />
              <span>Active Phases</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="text-2xl font-bold">
              {flowMetrics.mostActivePhase}
            </div>
            <p className="text-sm text-gray-600">
              Most common current phase
            </p>
            <div className="text-xs text-gray-500">
              Average progress: {flowMetrics.averageProgress.toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};