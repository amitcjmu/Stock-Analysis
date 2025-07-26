import React from 'react'
import { useState } from 'react'
import { useEffect, useCallback } from 'react'
import { Pause, StopCircle, Zap, Brain, Network, Target, Settings } from 'lucide-react'
import { Bot, Loader2, AlertTriangle, Activity, Clock, CheckCircle, XCircle, AlertCircle, Play, RefreshCw, Users, TrendingUp, Eye } from 'lucide-react'
import { Alert } from '@/components/ui/alert';
import { CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Card } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';

interface CrewInfo {
  name: string;
  description: string;
  process: string;
  crew_type: string;
}

interface AgentInfo {
  name: string;
  role: string;
  status: string;
  tools_count: number;
  backstory: string;
}

interface CrewDetails {
  id: string;
  name: string;
  description: string;
  status: string;
  progress: number;
  agent_count: number;
  current_phase: string;
}

interface FlowTemplate {
  flow_id: string;
  status: string;
  current_phase: string;
  progress: number;
  crews: CrewDetails[];
  started_at: string;
  performance_metrics: {
    overall_efficiency: number;
    crew_coordination: number;
    agent_collaboration: number;
  };
  events_count: number;
  last_event: string;
}

interface Phase2MonitoringData {
  available_crews: string[];
  crew_details: CrewInfo[];
  total_crews: number;
  system_health: {
    status: string;
    total_crews: number;
    active_agents: number;
    event_listener_active: boolean;
  };
  active_flows: FlowTemplate[];
  performance_summary: {
    avg_flow_efficiency: number;
    total_tasks_completed: number;
    success_rate: number;
    collaboration_effectiveness: number;
  };
}

const Phase2CrewMonitor: React.FC = () => {
  const [data, setData] = useState<Phase2MonitoringData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCrew, setSelectedCrew] = useState<string | null>(null);
  const [crewAgents, setCrewAgents] = useState<{[key: string]: AgentInfo[]}>({});

  const { getAuthHeaders } = useAuth();

  const fetchCrewAgents = useCallback(async (crewType: string) => {
    try {
      const response = await fetch(`/api/v1/monitoring/crews/${crewType}/status`, {
        headers: getAuthHeaders()
      });

      if (response.ok) {
        const crewData = await response.json();
        setCrewAgents(prev => ({
          ...prev,
          [crewType]: crewData.agents || []
        }));
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error(`Failed to fetch agents for crew ${crewType}:`, error);
      }
    }
  }, [getAuthHeaders]);

  const fetchCrewData = useCallback(async () => {
    try {
      setRefreshing(true);
      setError(null);

      // Fetch crew list
      const crewListResponse = await fetch('/api/v1/monitoring/crews/list', {
        headers: getAuthHeaders()
      });

      // Fetch system status
      const systemStatusResponse = await fetch('/api/v1/monitoring/crews/system/status', {
        headers: getAuthHeaders()
      });

      // Fetch active flows
      const activeFlowsResponse = await fetch('/api/v1/monitoring/crews/flows/active', {
        headers: getAuthHeaders()
      });

      const [crewListData, systemStatusData, activeFlowsData] = await Promise.all([
        crewListResponse.json(),
        systemStatusResponse.json(),
        activeFlowsResponse.json()
      ]);

      // Combine data
      const monitoringData: Phase2MonitoringData = {
        available_crews: crewListData.available_crews || [],
        crew_details: crewListData.crew_details || [],
        total_crews: crewListData.total_crews || 0,
        system_health: systemStatusData.system_health || {
          status: 'unknown',
          total_crews: 0,
          active_agents: 0,
          event_listener_active: false
        },
        active_flows: activeFlowsData.active_flows || [],
        performance_summary: systemStatusData.performance_summary || {
          avg_flow_efficiency: 0,
          total_tasks_completed: 0,
          success_rate: 0,
          collaboration_effectiveness: 0
        }
      };

      setData(monitoringData);

      // Pre-load agent data for all crews
      for (const crewType of monitoringData.available_crews) {
        try {
          await fetchCrewAgents(crewType);
        } catch (error) {
          if (process.env.NODE_ENV === 'development') {
            console.warn(`Failed to pre-load agents for ${crewType}:`, error);
          }
        }
      }

    } catch (err) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching crew data:', err);
      }
      setError(err instanceof Error ? err.message : 'Failed to fetch crew data');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  }, [getAuthHeaders, fetchCrewAgents]);

  useEffect(() => {
    fetchCrewData();
    const interval = setInterval(fetchCrewData, 30000); // Poll every 30 seconds (reduced frequency)
    return () => clearInterval(interval);
  }, [fetchCrewData]);

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      'healthy': 'bg-green-100 text-green-800',
      'ready': 'bg-blue-100 text-blue-800',
      'running': 'bg-blue-100 text-blue-800',
      'active': 'bg-green-100 text-green-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'error': 'bg-red-100 text-red-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'degraded': 'bg-orange-100 text-orange-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: string): JSX.Element => {
    switch (status) {
      case 'healthy':
      case 'ready':
      case 'active':
        return <CheckCircle className="h-4 w-4" />;
      case 'running':
        return <Play className="h-4 w-4" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'failed':
      case 'error':
        return <XCircle className="h-4 w-4" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-gray-600">Loading Phase 2 Crew System...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error loading crew monitoring data: {error}</p>
          <Button onClick={fetchCrewData} className="mt-2">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </Alert>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <p>No crew monitoring data available</p>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Phase 2 Crew System Monitor</h2>
          <p className="text-gray-600">Real-time monitoring of CrewAI crews, agents, and orchestration</p>
        </div>
        <div className="flex space-x-2">
          <Button
            onClick={fetchCrewData}
            disabled={refreshing}
            variant="outline"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <h3 className="text-2xl font-bold text-gray-900">
                <Badge className={getStatusColor(data.system_health.status)}>
                  {getStatusIcon(data.system_health.status)}
                  <span className="ml-1">{data.system_health.status}</span>
                </Badge>
              </h3>
            </div>
            <Activity className="h-8 w-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Available Crews</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.total_crews}</h3>
              <p className="text-xs text-gray-500">Ready for deployment</p>
            </div>
            <Users className="h-8 w-8 text-green-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Platform Agents</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.system_health.active_agents}</h3>
              <p className="text-xs text-gray-500">Registered & available</p>
            </div>
            <Bot className="h-8 w-8 text-purple-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Success Rate</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.performance_summary.success_rate.toFixed(1)}%</h3>
            </div>
            <TrendingUp className="h-8 w-8 text-green-600" />
          </div>
        </Card>
      </div>

      {/* Main Monitoring Interface */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">System Overview</TabsTrigger>
          <TabsTrigger value="crews">Crew Details</TabsTrigger>
          <TabsTrigger value="architecture">Architecture</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Available Crews */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Crews</h3>
              <div className="space-y-3">
                {data.crew_details.map((crew, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{crew.name}</p>
                      <p className="text-sm text-gray-600">{crew.description}</p>
                    </div>
                    <Badge className="bg-green-100 text-green-800">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Ready
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>

            {/* Performance Metrics */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Flow Efficiency</span>
                  <div className="flex items-center space-x-2">
                    <Progress value={data.performance_summary.avg_flow_efficiency} className="w-20" />
                    <span className="text-sm font-medium">{data.performance_summary.avg_flow_efficiency.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Collaboration</span>
                  <div className="flex items-center space-x-2">
                    <Progress value={data.performance_summary.collaboration_effectiveness} className="w-20" />
                    <span className="text-sm font-medium">{data.performance_summary.collaboration_effectiveness.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Tasks Completed</span>
                  <span className="text-sm font-medium">{data.performance_summary.total_tasks_completed}</span>
                </div>
              </div>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="crews" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.available_crews.map((crewType) => {
              const crewInfo = data.crew_details.find(c => c.crew_type === crewType);
              const agents = crewAgents[crewType] || [];

              return (
                <Card key={crewType} className="p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-900">{crewInfo?.name || crewType}</h4>
                    <Badge className="bg-blue-100 text-blue-800">
                      <Users className="h-3 w-3 mr-1" />
                      Ready
                    </Badge>
                  </div>

                  <p className="text-sm text-gray-600 mb-3">{crewInfo?.description}</p>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">
                      Agents: {agents.length > 0 ? agents.length : '2 (estimated)'}
                    </span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        if (selectedCrew === crewType) {
                          setSelectedCrew(null);
                        } else {
                          setSelectedCrew(crewType);
                          if (!agents.length) {
                            fetchCrewAgents(crewType);
                          }
                        }
                      }}
                    >
                      <Eye className="h-3 w-3 mr-1" />
                      {selectedCrew === crewType ? 'Hide' : 'Details'}
                    </Button>
                  </div>

                  {selectedCrew === crewType && (
                    <div className="mt-3 pt-3 border-t space-y-2">
                      <p className="text-sm font-medium text-gray-700">Agents:</p>
                      {agents.length > 0 ? (
                        agents.map((agent, idx) => (
                          <div key={idx} className="bg-gray-50 p-2 rounded text-xs">
                            <p className="font-medium">{agent.name}</p>
                            <p className="text-gray-600">{agent.role}</p>
                            <p className="text-gray-500">Tools: {agent.tools_count}</p>
                            {agent.backstory && (
                              <p className="text-gray-500 text-xs mt-1">{agent.backstory}</p>
                            )}
                          </div>
                        ))
                      ) : (
                        <div className="bg-gray-50 p-2 rounded text-xs">
                          <p className="text-gray-500">Loading agent details...</p>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </TabsContent>

        <TabsContent value="architecture" className="space-y-4">
          {data.active_flows.length > 0 && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Discovery Flow Architecture</h3>
              <div className="space-y-4">
                {data.active_flows[0].crews.map((crew) => (
                  <div key={crew.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">{crew.name}</h4>
                      <p className="text-sm text-gray-600">{crew.description}</p>
                      <p className="text-xs text-gray-500 mt-1">{crew.agent_count} agents ready</p>
                    </div>
                    <Badge className={getStatusColor(crew.status)}>
                      {getStatusIcon(crew.status)}
                      <span className="ml-1">{crew.status}</span>
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Phase2CrewMonitor;
