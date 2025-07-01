import React from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Activity, 
  Clock, 
  Target,
  Zap,
  Users,
  Brain
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import type { Crew, Agent } from '../types';
import { calculateAverageMetrics } from '../utils/agentDataProcessor';

interface AgentMetricsProps {
  crews: Crew[];
}

export const AgentMetrics: React.FC<AgentMetricsProps> = ({
  crews
}) => {
  const metrics = calculateAverageMetrics(crews);
  const allAgents = crews.flatMap(crew => crew.agents);
  
  // Calculate additional metrics
  const totalTasks = allAgents.reduce((sum, agent) => sum + agent.performance.tasks_completed, 0);
  const avgSuccessRate = allAgents.length > 0 ? 
    allAgents.reduce((sum, agent) => sum + agent.performance.success_rate, 0) / allAgents.length : 0;
  const avgResponseTime = allAgents.length > 0 ?
    allAgents.reduce((sum, agent) => sum + agent.performance.avg_response_time, 0) / allAgents.length : 0;
  
  // Collaboration metrics
  const collaboratingAgents = allAgents.filter(agent => agent.collaboration.is_collaborating).length;
  const collaborationRate = allAgents.length > 0 ? (collaboratingAgents / allAgents.length) * 100 : 0;

  if (crews.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <BarChart3 className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Metrics Available</h3>
          <p className="text-gray-600 text-center">
            Start a discovery flow to see detailed agent performance metrics.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <Target className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(avgSuccessRate * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-600">
              Average across all agents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tasks</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {totalTasks}
            </div>
            <p className="text-xs text-gray-600">
              Completed across all agents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response</CardTitle>
            <Zap className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {avgResponseTime.toFixed(1)}s
            </div>
            <p className="text-xs text-gray-600">
              Average response time
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {metrics.activeAgents}
            </div>
            <p className="text-xs text-gray-600">
              Out of {metrics.totalAgents} total
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Trends */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <span>Performance Metrics</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Success Rate Distribution */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">Overall Success Rate</span>
                <span className="text-sm font-bold text-green-600">
                  {(avgSuccessRate * 100).toFixed(1)}%
                </span>
              </div>
              <Progress value={avgSuccessRate * 100} className="h-2" />
              <p className="text-xs text-gray-600 mt-1">
                {avgSuccessRate >= 0.95 ? 'Excellent performance' : 
                 avgSuccessRate >= 0.85 ? 'Good performance' : 
                 avgSuccessRate >= 0.70 ? 'Fair performance' : 'Needs improvement'}
              </p>
            </div>

            {/* Collaboration Rate */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">Collaboration Rate</span>
                <span className="text-sm font-bold text-purple-600">
                  {collaborationRate.toFixed(1)}%
                </span>
              </div>
              <Progress value={collaborationRate} className="h-2" />
              <p className="text-xs text-gray-600 mt-1">
                {collaboratingAgents} of {allAgents.length} agents currently collaborating
              </p>
            </div>

            {/* Agent Utilization */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">Agent Utilization</span>
                <span className="text-sm font-bold text-orange-600">
                  {metrics.totalAgents > 0 ? ((metrics.activeAgents / metrics.totalAgents) * 100).toFixed(1) : 0}%
                </span>
              </div>
              <Progress 
                value={metrics.totalAgents > 0 ? (metrics.activeAgents / metrics.totalAgents) * 100 : 0} 
                className="h-2" 
              />
              <p className="text-xs text-gray-600 mt-1">
                {metrics.activeAgents} active out of {metrics.totalAgents} available agents
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Crew Performance Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="h-5 w-5 text-purple-600" />
            <span>Crew Performance</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {crews.map((crew) => {
              const crewSuccessRate = crew.agents.length > 0 ?
                crew.agents.reduce((sum, agent) => sum + agent.performance.success_rate, 0) / crew.agents.length : 0;
              const activeAgentsInCrew = crew.agents.filter(agent => agent.status === 'active').length;
              
              return (
                <div key={crew.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-gray-900">{crew.name}</h4>
                      <p className="text-sm text-gray-600">
                        {crew.agents.length} agents • {activeAgentsInCrew} active
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-blue-600">
                        {(crewSuccessRate * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-600">Success Rate</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <div className="font-semibold text-green-600">
                        {(crew.collaboration_metrics.internal_effectiveness * 100).toFixed(1)}%
                      </div>
                      <div className="text-gray-600">Internal Effectiveness</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-purple-600">
                        {(crew.collaboration_metrics.cross_crew_sharing * 100).toFixed(1)}%
                      </div>
                      <div className="text-gray-600">Cross-Crew Sharing</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-blue-600">
                        {(crew.collaboration_metrics.memory_utilization * 100).toFixed(1)}%
                      </div>
                      <div className="text-gray-600">Memory Utilization</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};