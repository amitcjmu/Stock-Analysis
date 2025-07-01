import React from 'react';
import { 
  Activity, 
  Users, 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  Zap,
  Brain,
  Network,
  Target
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { FlowCrewAgentData } from '../types';
import { calculateAverageMetrics } from '../utils/agentDataProcessor';

interface AgentStatusProps {
  data: FlowCrewAgentData | null;
}

export const AgentStatus: React.FC<AgentStatusProps> = ({
  data
}) => {
  if (!data) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Activity className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-600 text-center">
            Agent status information is not available at the moment.
          </p>
        </CardContent>
      </Card>
    );
  }

  const allCrews = data.active_flows.flatMap(flow => flow.crews);
  const metrics = calculateAverageMetrics(allCrews);
  
  const systemHealthColor = data.system_health.status === 'healthy' ? 'text-green-600' : 
                           data.system_health.status === 'degraded' ? 'text-yellow-600' : 
                           'text-red-600';

  return (
    <div className="space-y-6">
      {/* System Health Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className={`h-5 w-5 ${systemHealthColor}`} />
            <span>System Health</span>
            <Badge className={`ml-2 ${
              data.system_health.status === 'healthy' ? 'bg-green-100 text-green-800' :
              data.system_health.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {data.system_health.status.toUpperCase()}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {data.system_health.total_flows}
              </div>
              <div className="text-sm text-gray-600">Active Flows</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {data.system_health.active_crews}
              </div>
              <div className="text-sm text-gray-600">Available Crews</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {data.system_health.active_agents}
              </div>
              <div className="text-sm text-gray-600">Total Agents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {metrics.activeAgents}
              </div>
              <div className="text-sm text-gray-600">Active Now</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="h-5 w-5 text-blue-600" />
            <span>Performance Summary</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Success Rate */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">Overall Success Rate</span>
                <span className="text-sm font-bold text-green-600">
                  {data.performance_summary.success_rate.toFixed(1)}%
                </span>
              </div>
              <Progress value={data.performance_summary.success_rate} className="h-2" />
            </div>

            {/* Collaboration Effectiveness */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">Collaboration Effectiveness</span>
                <span className="text-sm font-bold text-purple-600">
                  {(data.performance_summary.collaboration_effectiveness * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={data.performance_summary.collaboration_effectiveness * 100} className="h-2" />
            </div>

            {/* Flow Efficiency */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">Average Flow Efficiency</span>
                <span className="text-sm font-bold text-blue-600">
                  {(data.performance_summary.avg_flow_efficiency * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={data.performance_summary.avg_flow_efficiency * 100} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Agent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-green-600" />
              <span>Agent Activity</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Tasks Completed</span>
                <span className="font-bold text-green-600">
                  {data.performance_summary.total_tasks_completed}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active Agents</span>
                <span className="font-bold text-blue-600">
                  {metrics.activeAgents} / {metrics.totalAgents}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Agent Utilization</span>
                <span className="font-bold text-purple-600">
                  {metrics.totalAgents > 0 ? ((metrics.activeAgents / metrics.totalAgents) * 100).toFixed(1) : 0}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Collaboration Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Network className="h-5 w-5 text-purple-600" />
              <span>Collaboration</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Cross-Crew Sharing</span>
                <span className="font-bold text-purple-600">
                  {(metrics.avgCollaboration * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Internal Effectiveness</span>
                <span className="font-bold text-green-600">
                  {(metrics.avgEfficiency * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Memory Utilization</span>
                <span className="font-bold text-blue-600">
                  {(metrics.avgMemoryUtilization * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Event Listener Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-orange-600" />
            <span>Real-time Monitoring</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`h-3 w-3 rounded-full ${
                data.system_health.event_listener_active ? 'bg-green-500 animate-pulse' : 'bg-red-500'
              }`} />
              <span className="text-sm text-gray-900">Event Listener</span>
            </div>
            <Badge className={
              data.system_health.event_listener_active ? 
              'bg-green-100 text-green-800' : 
              'bg-red-100 text-red-800'
            }>
              {data.system_health.event_listener_active ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          <p className="text-xs text-gray-600 mt-2">
            {data.system_health.event_listener_active ? 
              'Real-time monitoring is active and receiving agent events.' :
              'Real-time monitoring is currently unavailable.'
            }
          </p>
        </CardContent>
      </Card>
    </div>
  );
};