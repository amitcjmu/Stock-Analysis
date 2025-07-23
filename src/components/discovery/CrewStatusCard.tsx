import React from 'react'
import { useState } from 'react'
import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Users, 
  Activity,
  Brain,
  Crown,
  Network,
  Lightbulb,
  Play,
  Pause,
  RotateCcw,
  TrendingUp,
  Eye,
  Timer
} from 'lucide-react';

interface AgentStatus {
  name: string;
  role: string;
  status: 'idle' | 'active' | 'completed' | 'error';
  isManager?: boolean;
  currentTask?: string;
  progress?: number;
  collaborations?: number;
  performance?: {
    tasks_completed: number;
    success_rate: number;
    avg_duration_seconds: number;
  };
  last_activity?: string;
}

interface CrewStatusData {
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  progress: number;
  agents: AgentStatus[];
  manager?: string;
  started_at?: string;
  completed_at?: string;
  current_phase?: string;
  collaboration_metrics?: {
    intra_crew_score: number;
    cross_crew_score: number;
    memory_sharing_active: boolean;
    knowledge_utilization: number;
  };
  performance_metrics?: {
    execution_time_seconds: number;
    success_rate: number;
    resource_utilization: number;
    quality_score: number;
  };
  planning_status?: {
    strategy: string;
    coordination_score: number;
    adaptive_adjustments: number;
  };
}

interface CrewStatusCardProps {
  crewData: CrewStatusData;
  onAction?: (action: string, crewName: string) => void;
  showDetailedView?: boolean;
  refreshInterval?: number;
}

const CrewStatusCard: React.FC<CrewStatusCardProps> = ({
  crewData,
  onAction,
  showDetailedView = false,
  refreshInterval = 30000 // 30 seconds for production performance
}) => {
  const [isExpanded, setIsExpanded] = useState(showDetailedView);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdated(new Date());
    }, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: 'secondary',
      running: 'default',
      completed: 'outline',
      failed: 'destructive',
      paused: 'outline'
    } as const;
    
    const colors = {
      pending: 'bg-gray-100 text-gray-700',
      running: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      failed: 'bg-red-100 text-red-700',
      paused: 'bg-yellow-100 text-yellow-700'
    } as const;
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'secondary'} 
             className={colors[status as keyof typeof colors] || ''}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const getExecutionTime = (): string => {
    if (!crewData.started_at) return '0s';
    const start = new Date(crewData.started_at);
    const end = crewData.completed_at ? new Date(crewData.completed_at) : new Date();
    return formatDuration(Math.floor((end.getTime() - start.getTime()) / 1000));
  };

  const handleAction = (action: string) => {
    if (onAction) {
      onAction(action, crewData.name);
    }
  };

  const AgentCard: React.FC<{ agent: AgentStatus }> = ({ agent }) => (
    <div className={`p-3 rounded-lg border transition-colors ${
      agent.isManager 
        ? 'border-yellow-200 bg-yellow-50' 
        : agent.status === 'active' 
          ? 'border-blue-200 bg-blue-50'
          : 'border-gray-200 bg-gray-50'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {agent.isManager && <Crown className="h-4 w-4 text-yellow-600" />}
          <span className="font-medium text-sm">{agent.name}</span>
          {getStatusIcon(agent.status)}
        </div>
        <div className="flex items-center gap-2">
          {agent.collaborations && (
            <Badge variant="outline" className="text-xs">
              {agent.collaborations} collab
            </Badge>
          )}
          {agent.progress && (
            <Badge variant="outline" className="text-xs">
              {agent.progress}%
            </Badge>
          )}
        </div>
      </div>
      
      <p className="text-xs text-gray-600 mb-1">{agent.role}</p>
      
      {agent.currentTask && (
        <p className="text-xs text-blue-600 italic mb-2">{agent.currentTask}</p>
      )}
      
      {agent.performance && (
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="font-medium">{agent.performance.tasks_completed}</div>
            <div className="text-gray-500">Tasks</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{Math.round(agent.performance.success_rate * 100)}%</div>
            <div className="text-gray-500">Success</div>
          </div>
          <div className="text-center">
            <div className="font-medium">{formatDuration(agent.performance.avg_duration_seconds)}</div>
            <div className="text-gray-500">Avg Time</div>
          </div>
        </div>
      )}
      
      {agent.last_activity && (
        <div className="text-xs text-gray-500 mt-2">
          Last: {new Date(agent.last_activity).toLocaleTimeString()}
        </div>
      )}
    </div>
  );

  return (
    <Card className={`transition-all duration-300 ${
      crewData.status === 'running' ? 'border-blue-500 shadow-md' : 
      crewData.status === 'completed' ? 'border-green-500' :
      crewData.status === 'failed' ? 'border-red-500' :
      crewData.status === 'paused' ? 'border-yellow-500' : ''
    }`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <CardTitle className="text-lg">{crewData.name}</CardTitle>
              {crewData.manager && (
                <Badge variant="outline" className="text-xs">
                  Manager: {crewData.manager}
                </Badge>
              )}
              {getStatusBadge(crewData.status)}
            </div>
            
            {crewData.current_phase && (
              <CardDescription className="text-sm">
                Current Phase: {crewData.current_phase}
              </CardDescription>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              <Eye className="h-4 w-4" />
              {isExpanded ? 'Collapse' : 'Expand'}
            </Button>
            
            {crewData.status === 'running' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('pause')}
              >
                <Pause className="h-4 w-4" />
              </Button>
            )}
            
            {crewData.status === 'paused' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('resume')}
              >
                <Play className="h-4 w-4" />
              </Button>
            )}
            
            {(crewData.status === 'failed' || crewData.status === 'completed') && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleAction('restart')}
              >
                <RotateCcw className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-4">
          {/* Progress Bar */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span>Progress</span>
              <span>{crewData.progress}%</span>
            </div>
            <Progress value={crewData.progress} className="h-2" />
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Users className="h-3 w-3" />
                <span className="font-medium">{crewData.agents.length}</span>
              </div>
              <div className="text-gray-500 text-xs">Agents</div>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Timer className="h-3 w-3" />
                <span className="font-medium">{getExecutionTime()}</span>
              </div>
              <div className="text-gray-500 text-xs">Runtime</div>
            </div>
            
            {crewData.collaboration_metrics && (
              <>
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Network className="h-3 w-3" />
                    <span className="font-medium">{crewData.collaboration_metrics.intra_crew_score}/10</span>
                  </div>
                  <div className="text-gray-500 text-xs">Collaboration</div>
                </div>
                
                <div className="text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    <Brain className="h-3 w-3" />
                    <span className="font-medium">
                      {crewData.collaboration_metrics.memory_sharing_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="text-gray-500 text-xs">Memory</div>
                </div>
              </>
            )}
          </div>

          {/* Expanded View */}
          {isExpanded && (
            <div className="space-y-4 pt-4 border-t">
              {/* Collaboration Metrics */}
              {crewData.collaboration_metrics && (
                <div>
                  <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                    <Network className="h-4 w-4" />
                    Collaboration Metrics
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span>Intra-crew</span>
                        <span>{crewData.collaboration_metrics.intra_crew_score}/10</span>
                      </div>
                      <Progress value={crewData.collaboration_metrics.intra_crew_score * 10} className="h-1" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span>Cross-crew</span>
                        <span>{crewData.collaboration_metrics.cross_crew_score}/10</span>
                      </div>
                      <Progress value={crewData.collaboration_metrics.cross_crew_score * 10} className="h-1" />
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span>Knowledge</span>
                        <span>{crewData.collaboration_metrics.knowledge_utilization}/10</span>
                      </div>
                      <Progress value={crewData.collaboration_metrics.knowledge_utilization * 10} className="h-1" />
                    </div>
                    <div className="flex items-center gap-2">
                      <Brain className="h-3 w-3" />
                      <span>Memory Sharing</span>
                      <Badge variant={crewData.collaboration_metrics.memory_sharing_active ? 'default' : 'secondary'} className="text-xs">
                        {crewData.collaboration_metrics.memory_sharing_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                </div>
              )}

              {/* Performance Metrics */}
              {crewData.performance_metrics && (
                <div>
                  <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Performance Metrics
                  </h4>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                    <div className="text-center">
                      <div className="font-medium">{Math.round(crewData.performance_metrics.success_rate * 100)}%</div>
                      <div className="text-gray-500 text-xs">Success Rate</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{Math.round(crewData.performance_metrics.resource_utilization * 100)}%</div>
                      <div className="text-gray-500 text-xs">Resource Use</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{crewData.performance_metrics.quality_score.toFixed(1)}/10</div>
                      <div className="text-gray-500 text-xs">Quality Score</div>
                    </div>
                    <div className="text-center">
                      <div className="font-medium">{formatDuration(crewData.performance_metrics.execution_time_seconds)}</div>
                      <div className="text-gray-500 text-xs">Exec Time</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Planning Status */}
              {crewData.planning_status && (
                <div>
                  <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    Planning Status
                  </h4>
                  <div className="text-sm space-y-2">
                    <div className="flex justify-between">
                      <span>Strategy:</span>
                      <Badge variant="outline" className="text-xs">{crewData.planning_status.strategy}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Coordination Score:</span>
                      <span>{crewData.planning_status.coordination_score}/10</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Adaptive Adjustments:</span>
                      <span>{crewData.planning_status.adaptive_adjustments}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Agent Details */}
              <div>
                <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  Agent Status ({crewData.agents.length})
                </h4>
                <div className="space-y-3">
                  {crewData.agents.map((agent, index) => (
                    <AgentCard key={index} agent={agent} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Last Updated */}
          <div className="text-xs text-gray-500 text-center pt-2 border-t">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default CrewStatusCard; 