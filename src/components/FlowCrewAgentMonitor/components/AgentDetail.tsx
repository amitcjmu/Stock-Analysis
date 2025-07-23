import React from 'react';
import { 
  Bot, 
  Activity, 
  Clock, 
  TrendingUp, 
  Network, 
  Brain,
  CheckCircle,
  AlertTriangle,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Agent } from '../types';
import { getStatusColor } from '../utils/agentDataProcessor'
import { getStatusIcon, formatDuration } from '../utils/agentDataProcessor'

interface AgentDetailProps {
  agent: Agent | null;
  crewName?: string;
}

export const AgentDetail: React.FC<AgentDetailProps> = ({
  agent,
  crewName
}) => {
  if (!agent) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Bot className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Agent Selected</h3>
          <p className="text-gray-600 text-center">
            Select an agent from the list to view detailed information and performance metrics.
          </p>
        </CardContent>
      </Card>
    );
  }

  const successRatePercentage = agent.performance.success_rate * 100;

  return (
    <div className="space-y-6">
      {/* Agent Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Bot className="h-12 w-12 text-blue-600" />
                {agent.status === 'active' && (
                  <div className="absolute -top-1 -right-1 h-4 w-4 bg-green-500 rounded-full animate-pulse" />
                )}
              </div>
              <div>
                <CardTitle className="text-2xl flex items-center space-x-2">
                  <span>{agent.name}</span>
                  {agent.collaboration.is_collaborating && (
                    <Network className="h-5 w-5 text-purple-600" />
                  )}
                </CardTitle>
                <p className="text-gray-600">
                  {agent.role} {crewName ? `• ${crewName}` : ''}
                </p>
              </div>
            </div>
            
            <Badge className={`${getStatusColor(agent.status)} text-lg px-4 py-2`}>
              {getStatusIcon(agent.status)} {agent.status.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {/* Current Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <span>Current Activity</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Current Task</h4>
              <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                {agent.current_task}
              </p>
            </div>
            
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2 text-gray-600">
                <Clock className="h-4 w-4" />
                <span>Last activity: {formatDuration(agent.last_activity)} ago</span>
              </div>
              {agent.status === 'active' && (
                <div className="flex items-center space-x-2 text-green-600">
                  <div className="h-3 w-3 bg-green-500 rounded-full animate-pulse" />
                  <span className="font-medium">Currently Active</span>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <span>Performance Metrics</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Success Rate */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">Success Rate</span>
                <span className="text-sm font-bold text-green-600">
                  {successRatePercentage.toFixed(1)}%
                </span>
              </div>
              <Progress value={successRatePercentage} className="h-2" />
              <p className="text-xs text-gray-600 mt-1">
                {successRatePercentage >= 95 ? 'Excellent' : 
                 successRatePercentage >= 85 ? 'Good' : 
                 successRatePercentage >= 70 ? 'Fair' : 'Needs Improvement'}
              </p>
            </div>

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-1">
                  {agent.performance.tasks_completed}
                </div>
                <div className="text-sm text-gray-600">Tasks Completed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-1">
                  {agent.performance.avg_response_time.toFixed(1)}s
                </div>
                <div className="text-sm text-gray-600">Avg Response Time</div>
              </div>
            </div>

            {/* Performance Indicators */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className={`text-center p-2 rounded ${
                successRatePercentage >= 95 ? 'bg-green-100 text-green-800' : 
                successRatePercentage >= 85 ? 'bg-yellow-100 text-yellow-800' : 
                'bg-red-100 text-red-800'
              }`}>
                {successRatePercentage >= 95 ? <CheckCircle className="h-4 w-4 mx-auto mb-1" /> : 
                 <AlertTriangle className="h-4 w-4 mx-auto mb-1" />}
                Reliability
              </div>
              <div className={`text-center p-2 rounded ${
                agent.performance.avg_response_time <= 2 ? 'bg-green-100 text-green-800' :
                agent.performance.avg_response_time <= 4 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                <Zap className="h-4 w-4 mx-auto mb-1" />
                Speed
              </div>
              <div className={`text-center p-2 rounded ${
                agent.performance.tasks_completed >= 20 ? 'bg-green-100 text-green-800' :
                agent.performance.tasks_completed >= 10 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                <Activity className="h-4 w-4 mx-auto mb-1" />
                Productivity
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Collaboration Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="h-5 w-5 text-purple-600" />
            <span>Collaboration</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {agent.collaboration.is_collaborating ? (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-3">
                  <Network className="h-5 w-5 text-purple-600" />
                  <span className="font-medium text-purple-900">
                    Currently Collaborating
                  </span>
                </div>
                {agent.collaboration.collaboration_partner && (
                  <div className="mb-2">
                    <span className="text-sm text-purple-700">
                      Partner: <strong>{agent.collaboration.collaboration_partner}</strong>
                    </span>
                  </div>
                )}
                <div className="text-sm text-purple-600">
                  Shared memory access: {agent.collaboration.shared_memory_access ? 'Enabled' : 'Disabled'}
                </div>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Brain className="h-5 w-5 text-gray-600" />
                  <span className="font-medium text-gray-900">
                    Working Independently
                  </span>
                </div>
                <p className="text-sm text-gray-600">
                  Agent is currently working on individual tasks without active collaboration.
                </p>
                <div className="text-sm text-gray-500 mt-2">
                  Shared memory access: {agent.collaboration.shared_memory_access ? 'Available' : 'Not Available'}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};