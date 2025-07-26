import type React from 'react';
import { XCircle } from 'lucide-react'
import { Bot, Loader2, AlertTriangle, Activity, Clock, CheckCircle, AlertCircle } from 'lucide-react'
import { useAgentMonitor } from '@/hooks/useAgentMonitor';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

interface AgentMonitorResponse {
  success: boolean;
  data: {
    timestamp: string;
    system_status: string;
    active_agents: {
      total: number;
      active: number;
      idle: number;
      error: number;
    };
    crew_status: {
      [key: string]: {
        status: string;
        progress: number;
        agents: string[];
        last_activity: string | null;
      };
    };
    performance_metrics: {
      avg_response_time: number;
      success_rate: number;
      total_tasks_completed: number;
      tasks_in_progress: number;
      failed_tasks: number;
    };
    recent_activities: Array<{
      timestamp: string;
      agent: string;
      action: string;
      status: string;
      details: string;
    }>;
    resource_usage: {
      cpu_usage: number;
      memory_usage: number;
      api_calls_per_minute: number;
      tokens_consumed: number;
    };
    alerts: Array<{
      severity: string;
      message: string;
    }>;
    context: {
      client_id: string | null;
      engagement_id: string | null;
      user_id: string | null;
    };
  };
  message: string;
}

const AgentMonitor = (): JSX.Element => {
  const { data, isLoading, isError, error } = useAgentMonitor({
    enabled: true,
    polling: false // Disable aggressive polling
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-gray-600">Loading agent status...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error loading agent data: {error instanceof Error ? error.message : 'Unknown error'}</p>
        </Alert>
      </div>
    );
  }

  if (!data?.success || !data?.data) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>No agent monitoring data available</p>
        </Alert>
      </div>
    );
  }

  const monitorData = data.data;

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      'active': 'bg-green-100 text-green-800',
      'idle': 'bg-yellow-100 text-yellow-800',
      'error': 'bg-red-100 text-red-800',
      'pending': 'bg-blue-100 text-blue-800',
      'healthy': 'bg-green-100 text-green-800',
      'success': 'bg-green-100 text-green-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'warning': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status.toLowerCase()] || 'bg-gray-100 text-gray-800';
  };

  const formatTime = (timestamp: string | null): any => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatPercentage = (value: number): any => {
    return Math.round(value * 100);
  };

  return (
    <div className="space-y-6">
      {/* System Health Alert */}
      {monitorData.alerts && monitorData.alerts.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <div className="ml-2">
            <p className="font-medium">System Alerts</p>
            <ul className="mt-1 text-sm list-disc list-inside">
              {monitorData.alerts.map((alert, index) => (
                <li key={index}>{alert.message}</li>
              ))}
            </ul>
          </div>
        </Alert>
      )}

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Agents</p>
              <h3 className="text-2xl font-bold text-gray-900">
                {monitorData.active_agents.active}/{monitorData.active_agents.total}
              </h3>
            </div>
            <Bot className="h-8 w-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tasks Completed</p>
              <h3 className="text-2xl font-bold text-gray-900">
                {monitorData.performance_metrics.total_tasks_completed}
              </h3>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <h3 className="text-2xl font-bold text-gray-900">
                {formatPercentage(monitorData.performance_metrics.success_rate)}%
              </h3>
            </div>
            <Activity className="h-8 w-8 text-purple-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Status</p>
              <h3 className="text-lg font-bold text-gray-900">{monitorData.system_status}</h3>
            </div>
            <Badge className={getStatusColor(monitorData.system_status)}>
              {monitorData.system_status}
            </Badge>
          </div>
        </Card>
      </div>

      {/* Crew Status Grid */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Crew Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(monitorData.crew_status).map(([crewName, crew]) => (
              <Card key={crewName} className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {crewName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </h3>
                    <p className="text-sm text-gray-500">{crew.agents.length} agents</p>
                  </div>
                  <Badge className={getStatusColor(crew.status)}>{crew.status}</Badge>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progress</span>
                      <span>{crew.progress}%</span>
                    </div>
                    <Progress value={crew.progress} className="h-2" />
                  </div>

                  <div className="text-sm">
                    <span className="text-gray-600">Agents:</span>
                    <div className="mt-1">
                      {crew.agents.map((agent, index) => (
                        <Badge key={index} variant="outline" className="mr-1 mb-1">
                          {agent}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center text-sm text-gray-500">
                    <Clock className="h-4 w-4 mr-1" />
                    Last activity: {formatTime(crew.last_activity)}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </Card>

      {/* Resource Usage */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Resource Usage</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">CPU Usage</p>
              <div className="text-2xl font-bold text-gray-900">{monitorData.resource_usage.cpu_usage}%</div>
              <Progress value={monitorData.resource_usage.cpu_usage} className="h-2 mt-2" />
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Memory Usage</p>
              <div className="text-2xl font-bold text-gray-900">{monitorData.resource_usage.memory_usage}%</div>
              <Progress value={monitorData.resource_usage.memory_usage} className="h-2 mt-2" />
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">API Calls/min</p>
              <div className="text-2xl font-bold text-gray-900">{monitorData.resource_usage.api_calls_per_minute}</div>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">Tokens Used</p>
              <div className="text-2xl font-bold text-gray-900">{monitorData.resource_usage.tokens_consumed.toLocaleString()}</div>
            </div>
          </div>
        </div>
      </Card>

      {/* Recent Activities */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h2>
          <div className="space-y-3">
            {monitorData.recent_activities.map((activity, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-shrink-0">
                  <Badge className={getStatusColor(activity.status)}>{activity.status}</Badge>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">{activity.agent}</p>
                  <p className="text-sm text-gray-600">{activity.action}</p>
                  <p className="text-xs text-gray-500">{activity.details}</p>
                </div>
                <div className="text-xs text-gray-500">
                  {formatTime(activity.timestamp)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AgentMonitor;
