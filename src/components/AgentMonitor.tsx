import React from 'react';
import { Bot, Loader2, AlertTriangle, Activity, Clock, Memory, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useAgentMonitor } from '@/hooks/useAgentMonitor';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

const AgentMonitor = () => {
  const { data, isLoading, isError, error } = useAgentMonitor();

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
          <p>Error loading agent data: {error?.message}</p>
        </Alert>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    const colors = {
      'Active': 'bg-green-100 text-green-800',
      'Idle': 'bg-yellow-100 text-yellow-800',
      'Error': 'bg-red-100 text-red-800',
      'Offline': 'bg-gray-100 text-gray-800',
      'Success': 'bg-green-100 text-green-800',
      'Failed': 'bg-red-100 text-red-800',
      'In Progress': 'bg-blue-100 text-blue-800',
      'Healthy': 'bg-green-100 text-green-800',
      'Warning': 'bg-yellow-100 text-yellow-800',
      'Critical': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatBytes = (bytes: number) => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let value = bytes;
    let unitIndex = 0;
    
    while (value >= 1024 && unitIndex < units.length - 1) {
      value /= 1024;
      unitIndex++;
    }
    
    return `${value.toFixed(1)} ${units[unitIndex]}`;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="space-y-6">
      {/* System Health Alert */}
      {data.metrics.system_health.status !== 'Healthy' && (
        <Alert variant={data.metrics.system_health.status === 'Critical' ? 'destructive' : 'warning'}>
          <AlertCircle className="h-4 w-4" />
          <div className="ml-2">
            <p className="font-medium">System Health: {data.metrics.system_health.status}</p>
            <ul className="mt-1 text-sm list-disc list-inside">
              {data.metrics.system_health.issues.map((issue, index) => (
                <li key={index}>{issue}</li>
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
              <h3 className="text-2xl font-bold text-gray-900">{data.metrics.active_agents}/{data.metrics.total_agents}</h3>
            </div>
            <Bot className="h-8 w-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tasks Completed</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.metrics.total_tasks_completed}</h3>
            </div>
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.metrics.average_success_rate}%</h3>
            </div>
            <Activity className="h-8 w-8 text-purple-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.metrics.system_health.status}</h3>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(data.metrics.system_health.status)}`}>
              {data.metrics.system_health.status}
            </span>
          </div>
        </Card>
      </div>

      {/* Agent Status Grid */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.agents.map((agent) => (
              <Card key={agent.id} className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-medium text-gray-900">{agent.name}</h3>
                    <p className="text-sm text-gray-500">ID: {agent.id}</p>
                  </div>
                  <Badge className={getStatusColor(agent.status)}>{agent.status}</Badge>
                </div>

                <div className="space-y-3">
                  {agent.current_task && (
                    <div className="text-sm">
                      <span className="text-gray-600">Current Task:</span>
                      <span className="ml-2">{agent.current_task}</span>
                    </div>
                  )}

                  <div className="flex items-center text-sm">
                    <Clock className="h-4 w-4 text-gray-400 mr-2" />
                    <span>Last Active: {formatTime(agent.last_active)}</span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Success Rate</span>
                      <span>{agent.performance.success_rate}%</span>
                    </div>
                    <Progress value={agent.performance.success_rate} />
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center">
                      <Memory className="h-4 w-4 text-gray-400 mr-2" />
                      <span>Memory Usage</span>
                    </div>
                    <span>{formatBytes(agent.memory_usage.current)} / {formatBytes(agent.memory_usage.peak)}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </Card>

      {/* Recent Activities */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activities</h2>
          <div className="space-y-4">
            {data.recent_activities.map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">{activity.agent_name}</p>
                  <p className="text-sm text-gray-600">{activity.action}</p>
                  <p className="text-sm text-gray-500">{formatTime(activity.timestamp)}</p>
                </div>
                <Badge className={getStatusColor(activity.status)}>
                  {activity.status === 'Success' && <CheckCircle className="h-4 w-4 mr-1" />}
                  {activity.status === 'Failed' && <XCircle className="h-4 w-4 mr-1" />}
                  {activity.status === 'In Progress' && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                  {activity.status}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
};

export default AgentMonitor; 