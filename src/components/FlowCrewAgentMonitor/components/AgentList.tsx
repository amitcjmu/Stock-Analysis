import React from 'react';
import type { CheckCircle, AlertTriangle, Brain } from 'lucide-react'
import { Users, Bot, Activity, Clock, Network } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Progress } from '@/components/ui/progress';
import type { Agent, Crew } from '../types';
import type { getStatusColor } from '../utils/agentDataProcessor'
import { getStatusIcon, formatDuration } from '../utils/agentDataProcessor'

interface AgentListProps {
  crews: Crew[];
  onAgentSelect?: (agent: Agent) => void;
  selectedAgentId?: string;
}

export const AgentList: React.FC<AgentListProps> = ({
  crews,
  onAgentSelect,
  selectedAgentId
}) => {
  const allAgents = crews.flatMap(crew => 
    crew.agents.map(agent => ({ ...agent, crewName: crew.name, crewId: crew.id }))
  );

  if (allAgents.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Users className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Agents</h3>
          <p className="text-gray-600 text-center">
            No agents are currently active. Start a discovery flow to see agent activity.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center space-x-2">
          <Users className="h-5 w-5" />
          <span>Active Agents ({allAgents.length})</span>
        </h2>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="bg-green-50 text-green-700">
            {allAgents.filter(a => a.status === 'active').length} Active
          </Badge>
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            {allAgents.filter(a => a.status === 'idle').length} Idle
          </Badge>
        </div>
      </div>

      <div className="grid gap-4">
        {allAgents.map((agent) => (
          <Card 
            key={agent.id} 
            className={`border transition-all cursor-pointer hover:shadow-md ${
              selectedAgentId === agent.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
            }`}
            onClick={() => onAgentSelect?.(agent)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <Bot className="h-8 w-8 text-blue-600" />
                    {agent.status === 'active' && (
                      <div className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full animate-pulse" />
                    )}
                  </div>
                  <div>
                    <CardTitle className="text-lg flex items-center space-x-2">
                      <span>{agent.name}</span>
                      {agent.collaboration.is_collaborating && (
                        <Network className="h-4 w-4 text-purple-600" />
                      )}
                    </CardTitle>
                    <p className="text-sm text-gray-600">
                      {agent.crewName} • {agent.role}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(agent.status)}>
                    {getStatusIcon(agent.status)} {agent.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Current Task */}
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <Activity className="h-4 w-4 text-gray-600" />
                  <span className="text-sm font-medium text-gray-900">Current Task</span>
                </div>
                <p className="text-sm text-gray-700 pl-6">
                  {agent.current_task}
                </p>
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600">
                    {(agent.performance.success_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-gray-600">Success Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-blue-600">
                    {agent.performance.tasks_completed}
                  </div>
                  <div className="text-gray-600">Tasks Done</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-purple-600">
                    {agent.performance.avg_response_time.toFixed(1)}s
                  </div>
                  <div className="text-gray-600">Avg Response</div>
                </div>
              </div>

              {/* Collaboration Status */}
              {agent.collaboration.is_collaborating && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                  <div className="flex items-center space-x-2 mb-1">
                    <Network className="h-4 w-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-900">
                      Collaborating
                    </span>
                  </div>
                  {agent.collaboration.collaboration_partner && (
                    <p className="text-sm text-purple-700 pl-6">
                      With: {agent.collaboration.collaboration_partner}
                    </p>
                  )}
                  <div className="text-xs text-purple-600 pl-6 mt-1">
                    Shared memory access: {agent.collaboration.shared_memory_access ? 'Yes' : 'No'}
                  </div>
                </div>
              )}

              {/* Last Activity */}
              <div className="flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>Last activity: {formatDuration(agent.last_activity)} ago</span>
                </div>
                {agent.status === 'active' && (
                  <div className="flex items-center space-x-1 text-green-600">
                    <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                    <span>Live</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};