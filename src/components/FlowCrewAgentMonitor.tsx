import React, { useState, useEffect } from 'react';
import { 
  Bot, Loader2, AlertTriangle, Activity, Clock, CheckCircle, XCircle, 
  AlertCircle, Play, Pause, StopCircle, RefreshCw, Users, Zap,
  Brain, Network, Target, TrendingUp, Eye, Settings
} from 'lucide-react';
import { Alert } from '@/components/ui/alert';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useAuth } from '@/contexts/AuthContext';

type FlowStatus = 'running' | 'completed' | 'failed' | 'pending' | 'paused';
type CrewStatus = 'active' | 'completed' | 'failed' | 'pending' | 'paused';
type AgentStatus = 'active' | 'idle' | 'error' | 'completed' | 'paused';

interface Agent {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  current_task: string;
  performance: {
    success_rate: number;
    tasks_completed: number;
    avg_response_time: number;
  };
  collaboration: {
    is_collaborating: boolean;
    collaboration_partner?: string;
    shared_memory_access: boolean;
  };
  last_activity: string;
}

interface Crew {
  id: string;
  name: string;
  manager: string;
  status: CrewStatus;
  progress: number;
  agents: Agent[];
  current_phase: string;
  started_at: string;
  estimated_completion?: string;
  collaboration_metrics: {
    internal_effectiveness: number;
    cross_crew_sharing: number;
    memory_utilization: number;
  };
}

interface DiscoveryFlow {
  flow_id: string;
  status: FlowStatus;
  current_phase: string;
  progress: number;
  crews: Crew[];
  started_at: string;
  estimated_completion?: string;
  performance_metrics: {
    overall_efficiency: number;
    crew_coordination: number;
    agent_collaboration: number;
  };
  events_count: number;
  last_event: string;
}

interface FlowCrewAgentData {
  active_flows: DiscoveryFlow[];
  system_health: {
    status: string;
    total_flows: number;
    active_crews: number;
    active_agents: number;
    event_listener_active: boolean;
  };
  performance_summary: {
    avg_flow_efficiency: number;
    total_tasks_completed: number;
    success_rate: number;
    collaboration_effectiveness: number;
  };
}

const FlowCrewAgentMonitor: React.FC = () => {
  const [data, setData] = useState<FlowCrewAgentData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('flows');
  const [selectedFlow, setSelectedFlow] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  
  const { getContextHeaders } = useAuth();

  const fetchMonitoringData = async () => {
    try {
      setRefreshing(true);
      
      // Fetch active flows with crew and agent details
      const flowsResponse = await fetch('/api/v1/monitoring/crewai-flows', {
        headers: getContextHeaders()
      });
      
      if (!flowsResponse.ok) {
        throw new Error('Failed to fetch flows data');
      }
      
      const flowsData = await flowsResponse.json();
      
      // Transform the data to match our interface
      const activeFlows: DiscoveryFlow[] = [];
      
      if (flowsData.crewai_flows && flowsData.crewai_flows.active_flows) {
        for (const flow of flowsData.crewai_flows.active_flows) {
          try {
            // Get detailed crew monitoring for this flow
            const crewResponse = await fetch(`/api/v1/discovery/flow/crews/monitoring/${flow.session_id}`, {
              headers: getContextHeaders()
            });
            
            let crews: Crew[] = [];
            if (crewResponse.ok) {
              const crewData = await crewResponse.json();
              crews = transformCrewData(crewData);
            }
            
            activeFlows.push({
              flow_id: flow.session_id,
              status: flow.status,
              current_phase: flow.current_phase || 'initialization',
              progress: flow.progress_percentage || 0,
              crews,
              started_at: flow.started_at,
              estimated_completion: flow.estimated_completion,
              performance_metrics: {
                overall_efficiency: 0.85, // Mock for now
                crew_coordination: 0.78,
                agent_collaboration: 0.92
              },
              events_count: flow.events_count || 0,
              last_event: flow.last_event || new Date().toISOString()
            });
          } catch (flowError) {
            console.warn(`Failed to get details for flow ${flow.session_id}:`, flowError);
          }
        }
      }
      
      const monitoringData: FlowCrewAgentData = {
        active_flows: activeFlows,
        system_health: {
          status: flowsData.crewai_flows?.service_health?.status || 'unknown',
          total_flows: activeFlows.length,
          active_crews: activeFlows.reduce((sum, flow) => sum + flow.crews.length, 0),
          active_agents: activeFlows.reduce((sum, flow) => 
            sum + flow.crews.reduce((crewSum, crew) => crewSum + crew.agents.length, 0), 0),
          event_listener_active: true
        },
        performance_summary: {
          avg_flow_efficiency: activeFlows.reduce((sum, flow) => 
            sum + flow.performance_metrics.overall_efficiency, 0) / Math.max(activeFlows.length, 1),
          total_tasks_completed: 156, // Mock for now
          success_rate: 94.2,
          collaboration_effectiveness: 0.88
        }
      };
      
      setData(monitoringData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
      setRefreshing(false);
    }
  };

  const transformCrewData = (crewData: any): Crew[] => {
    const crews: Crew[] = [];
    
    if (crewData.crews) {
      const crewTypes = [
        { key: 'field_mapping', name: 'Field Mapping Crew', manager: 'Field Mapping Manager' },
        { key: 'data_cleansing', name: 'Data Cleansing Crew', manager: 'Data Quality Manager' },
        { key: 'inventory_building', name: 'Inventory Building Crew', manager: 'Inventory Manager' },
        { key: 'app_server_dependencies', name: 'App-Server Dependencies', manager: 'Dependency Manager' },
        { key: 'app_app_dependencies', name: 'App-App Dependencies', manager: 'Integration Manager' },
        { key: 'technical_debt', name: 'Technical Debt Crew', manager: 'Technical Debt Manager' }
      ];

      crewTypes.forEach(crewType => {
        const crewInfo = crewData.crews[crewType.key];
        if (crewInfo) {
          const agents: Agent[] = [];
          
          // Create agents based on crew type
          if (crewInfo.agents && Array.isArray(crewInfo.agents)) {
            crewInfo.agents.forEach((agentInfo: any, index: number) => {
              agents.push({
                id: `${crewType.key}_agent_${index}`,
                name: agentInfo.name || `${crewType.name} Agent ${index + 1}`,
                role: agentInfo.role || 'Specialist',
                status: agentInfo.status || 'idle',
                current_task: agentInfo.current_task || 'Waiting for assignment',
                performance: {
                  success_rate: agentInfo.performance?.success_rate || 95,
                  tasks_completed: agentInfo.performance?.tasks_completed || 12,
                  avg_response_time: agentInfo.performance?.avg_response_time || 2.3
                },
                collaboration: {
                  is_collaborating: agentInfo.collaboration?.is_collaborating || false,
                  collaboration_partner: agentInfo.collaboration?.partner,
                  shared_memory_access: agentInfo.collaboration?.memory_access || true
                },
                last_activity: agentInfo.last_activity || new Date().toISOString()
              });
            });
          } else {
            // Create default agents for crew structure
            const defaultAgents = getDefaultAgentsForCrew(crewType.key);
            agents.push(...defaultAgents);
          }

          crews.push({
            id: crewType.key,
            name: crewType.name,
            manager: crewType.manager,
            status: crewInfo.status || 'pending',
            progress: crewInfo.progress || 0,
            agents,
            current_phase: crewInfo.current_phase || 'initialization',
            started_at: crewInfo.started_at || new Date().toISOString(),
            estimated_completion: crewInfo.estimated_completion,
            collaboration_metrics: {
              internal_effectiveness: crewInfo.performance_metrics?.collaboration_score || 0.85,
              cross_crew_sharing: crewInfo.performance_metrics?.cross_crew_score || 0.72,
              memory_utilization: crewInfo.performance_metrics?.memory_score || 0.88
            }
          });
        }
      });
    }
    
    return crews;
  };

  const getDefaultAgentsForCrew = (crewKey: string): Agent[] => {
    const agentTemplates: Record<string, Array<{name: string, role: string}>> = {
      field_mapping: [
        { name: 'Schema Analysis Expert', role: 'Data Analyst' },
        { name: 'Attribute Mapping Specialist', role: 'Mapping Expert' }
      ],
      data_cleansing: [
        { name: 'Data Validation Expert', role: 'Quality Specialist' },
        { name: 'Data Standardization Specialist', role: 'Standards Expert' }
      ],
      inventory_building: [
        { name: 'Server Classification Expert', role: 'Infrastructure Analyst' },
        { name: 'Application Discovery Expert', role: 'App Portfolio Analyst' },
        { name: 'Device Classification Expert', role: 'Network Specialist' }
      ],
      app_server_dependencies: [
        { name: 'Application Topology Expert', role: 'Topology Analyst' },
        { name: 'Infrastructure Relationship Analyst', role: 'Dependency Expert' }
      ],
      app_app_dependencies: [
        { name: 'Application Integration Expert', role: 'Integration Analyst' },
        { name: 'API Dependency Analyst', role: 'API Specialist' }
      ],
      technical_debt: [
        { name: 'Legacy Technology Analyst', role: 'Tech Assessment Expert' },
        { name: 'Modernization Strategy Expert', role: 'Strategy Specialist' },
        { name: 'Risk Assessment Specialist', role: 'Risk Analyst' }
      ]
    };

    const templates = agentTemplates[crewKey] || [];
    return templates.map((template, index) => ({
      id: `${crewKey}_${index}`,
      name: template.name,
      role: template.role,
      status: 'idle' as AgentStatus,
      current_task: 'Awaiting crew activation',
      performance: {
        success_rate: 95 + Math.random() * 5,
        tasks_completed: Math.floor(Math.random() * 20) + 5,
        avg_response_time: 1.5 + Math.random() * 2
      },
      collaboration: {
        is_collaborating: false,
        shared_memory_access: true
      },
      last_activity: new Date().toISOString()
    }));
  };

  useEffect(() => {
    fetchMonitoringData();
    const interval = setInterval(fetchMonitoringData, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      'running': 'bg-blue-100 text-blue-800',
      'active': 'bg-green-100 text-green-800',
      'completed': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'error': 'bg-red-100 text-red-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'idle': 'bg-gray-100 text-gray-800',
      'paused': 'bg-orange-100 text-orange-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'active':
        return <Play className="h-4 w-4" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'failed':
      case 'error':
        return <XCircle className="h-4 w-4" />;
      case 'paused':
        return <Pause className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const handleFlowAction = async (flowId: string, action: 'pause' | 'resume' | 'stop') => {
    try {
      const response = await fetch(`/api/v1/discovery/flow/${flowId}/${action}`, {
        method: 'POST',
        headers: getContextHeaders()
      });
      
      if (response.ok) {
        await fetchMonitoringData(); // Refresh data
      }
    } catch (error) {
      console.error(`Failed to ${action} flow:`, error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-gray-600">Loading CrewAI Flow monitoring...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <p>Error loading monitoring data: {error}</p>
          <Button onClick={fetchMonitoringData} className="mt-2">
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
          <p>No monitoring data available</p>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Refresh */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">CrewAI Flow Monitor</h2>
          <p className="text-gray-600">Real-time monitoring of Discovery Flows, Crews, and Agents</p>
        </div>
        <Button 
          onClick={fetchMonitoringData} 
          disabled={refreshing}
          variant="outline"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Flows</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.system_health.total_flows}</h3>
            </div>
            <Network className="h-8 w-8 text-blue-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Crews</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.system_health.active_crews}</h3>
            </div>
            <Users className="h-8 w-8 text-green-600" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Active Agents</p>
              <h3 className="text-2xl font-bold text-gray-900">{data.system_health.active_agents}</h3>
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
          <TabsTrigger value="flows">Discovery Flows</TabsTrigger>
          <TabsTrigger value="crews">Crew Details</TabsTrigger>
          <TabsTrigger value="agents">Agent Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="flows" className="space-y-4">
          {data.active_flows.length === 0 ? (
            <Card className="p-8 text-center">
              <Network className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Flows</h3>
              <p className="text-gray-600">Start a Discovery Flow to see monitoring data here</p>
            </Card>
          ) : (
            data.active_flows.map((flow) => (
              <Card key={flow.flow_id} className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                      <Network className="h-5 w-5 mr-2 text-blue-600" />
                      Discovery Flow
                    </h3>
                    <p className="text-sm text-gray-500">ID: {flow.flow_id}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(flow.status)}>
                      {getStatusIcon(flow.status)}
                      <span className="ml-1">{flow.status}</span>
                    </Badge>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedFlow(selectedFlow === flow.flow_id ? null : flow.flow_id)}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      {selectedFlow === flow.flow_id ? 'Hide' : 'Details'}
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-600">Current Phase</p>
                    <p className="font-medium">{flow.current_phase}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Progress</p>
                    <div className="flex items-center space-x-2">
                      <Progress value={flow.progress} className="flex-1" />
                      <span className="text-sm font-medium">{flow.progress.toFixed(0)}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Started</p>
                    <p className="font-medium">{new Date(flow.started_at).toLocaleTimeString()}</p>
                  </div>
                </div>

                {/* Crew Status Overview */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
                  {flow.crews.map((crew) => (
                    <div key={crew.id} className="bg-gray-50 p-3 rounded-lg text-center">
                      <p className="text-xs font-medium text-gray-600">{crew.name}</p>
                      <Badge className={`${getStatusColor(crew.status)} text-xs mt-1`}>
                        {crew.status}
                      </Badge>
                      <p className="text-xs text-gray-500 mt-1">{crew.agents.length} agents</p>
                    </div>
                  ))}
                </div>

                {/* Flow Actions */}
                {flow.status === 'running' && (
                  <div className="mt-4 flex space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleFlowAction(flow.flow_id, 'pause')}
                    >
                      <Pause className="h-4 w-4 mr-1" />
                      Pause
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleFlowAction(flow.flow_id, 'stop')}
                    >
                      <StopCircle className="h-4 w-4 mr-1" />
                      Stop
                    </Button>
                  </div>
                )}

                {/* Expanded Details */}
                {selectedFlow === flow.flow_id && (
                  <div className="mt-6 border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-3">Performance Metrics</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <p className="text-sm text-blue-600">Overall Efficiency</p>
                        <p className="text-lg font-bold text-blue-900">
                          {(flow.performance_metrics.overall_efficiency * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="bg-green-50 p-3 rounded-lg">
                        <p className="text-sm text-green-600">Crew Coordination</p>
                        <p className="text-lg font-bold text-green-900">
                          {(flow.performance_metrics.crew_coordination * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="bg-purple-50 p-3 rounded-lg">
                        <p className="text-sm text-purple-600">Agent Collaboration</p>
                        <p className="text-lg font-bold text-purple-900">
                          {(flow.performance_metrics.agent_collaboration * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="crews" className="space-y-4">
          {data.active_flows.length === 0 ? (
            <Card className="p-8 text-center">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Crews</h3>
              <p className="text-gray-600">Crews will appear here when Discovery Flows are running</p>
            </Card>
          ) : (
            data.active_flows.map((flow) =>
              flow.crews.map((crew) => (
                <Card key={`${flow.flow_id}-${crew.id}`} className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                        <Users className="h-5 w-5 mr-2 text-green-600" />
                        {crew.name}
                      </h3>
                      <p className="text-sm text-gray-500">Manager: {crew.manager}</p>
                    </div>
                    <Badge className={getStatusColor(crew.status)}>
                      {getStatusIcon(crew.status)}
                      <span className="ml-1">{crew.status}</span>
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600">Progress</p>
                      <div className="flex items-center space-x-2">
                        <Progress value={crew.progress} className="flex-1" />
                        <span className="text-sm font-medium">{crew.progress.toFixed(0)}%</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Current Phase</p>
                      <p className="font-medium">{crew.current_phase}</p>
                    </div>
                  </div>

                  {/* Agents in this crew */}
                  <div className="space-y-2">
                    <h4 className="font-medium text-gray-900">Agents ({crew.agents.length})</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {crew.agents.map((agent) => (
                        <div key={agent.id} className="bg-gray-50 p-3 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <p className="font-medium text-sm">{agent.name}</p>
                            <Badge className={`${getStatusColor(agent.status)} text-xs`}>
                              {agent.status}
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">{agent.role}</p>
                          <p className="text-xs text-gray-500">{agent.current_task}</p>
                          <div className="flex items-center justify-between mt-2 text-xs">
                            <span>Success: {agent.performance.success_rate.toFixed(0)}%</span>
                            {agent.collaboration.is_collaborating && (
                              <span className="text-blue-600 flex items-center">
                                <Network className="h-3 w-3 mr-1" />
                                Collaborating
                              </span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Collaboration Metrics */}
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="bg-blue-50 p-3 rounded-lg">
                      <p className="text-xs text-blue-600">Internal Effectiveness</p>
                      <p className="text-sm font-bold text-blue-900">
                        {(crew.collaboration_metrics.internal_effectiveness * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-green-50 p-3 rounded-lg">
                      <p className="text-xs text-green-600">Cross-Crew Sharing</p>
                      <p className="text-sm font-bold text-green-900">
                        {(crew.collaboration_metrics.cross_crew_sharing * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="bg-purple-50 p-3 rounded-lg">
                      <p className="text-xs text-purple-600">Memory Utilization</p>
                      <p className="text-sm font-bold text-purple-900">
                        {(crew.collaboration_metrics.memory_utilization * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </Card>
              ))
            )
          )}
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          {data.active_flows.length === 0 ? (
            <Card className="p-8 text-center">
              <Bot className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Agents</h3>
              <p className="text-gray-600">Agents will appear here when Discovery Flows are running</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.active_flows.flatMap(flow =>
                flow.crews.flatMap(crew =>
                  crew.agents.map(agent => (
                    <Card key={`${flow.flow_id}-${crew.id}-${agent.id}`} className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-900">{agent.name}</h4>
                          <p className="text-sm text-gray-500">{agent.role}</p>
                        </div>
                        <Badge className={getStatusColor(agent.status)}>
                          {getStatusIcon(agent.status)}
                          <span className="ml-1">{agent.status}</span>
                        </Badge>
                      </div>

                      <div className="space-y-2 text-sm">
                        <div>
                          <p className="text-gray-600">Current Task:</p>
                          <p className="font-medium">{agent.current_task}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <p className="text-gray-600">Success Rate</p>
                            <p className="font-bold text-green-600">
                              {agent.performance.success_rate.toFixed(0)}%
                            </p>
                          </div>
                          <div>
                            <p className="text-gray-600">Tasks Done</p>
                            <p className="font-bold">{agent.performance.tasks_completed}</p>
                          </div>
                        </div>

                        <div>
                          <p className="text-gray-600">Avg Response</p>
                          <p className="font-medium">{agent.performance.avg_response_time.toFixed(1)}s</p>
                        </div>

                        {agent.collaboration.is_collaborating && (
                          <div className="bg-blue-50 p-2 rounded">
                            <p className="text-blue-600 text-xs flex items-center">
                              <Network className="h-3 w-3 mr-1" />
                              Collaborating
                              {agent.collaboration.collaboration_partner && 
                                ` with ${agent.collaboration.collaboration_partner}`
                              }
                            </p>
                          </div>
                        )}

                        {agent.collaboration.shared_memory_access && (
                          <div className="flex items-center text-xs text-gray-500">
                            <Brain className="h-3 w-3 mr-1" />
                            Shared Memory Access
                          </div>
                        )}
                      </div>

                      <div className="mt-3 text-xs text-gray-500">
                        Last Activity: {new Date(agent.last_activity).toLocaleTimeString()}
                      </div>
                    </Card>
                  ))
                )
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default FlowCrewAgentMonitor; 