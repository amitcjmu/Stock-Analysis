import React from 'react'
import { useState } from 'react'
import { 
  Bot, 
  RefreshCw, 
  Settings, 
  Eye,
  Activity,
  BarChart3,
  Users
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';

// Import Phase2CrewMonitor for fallback
import Phase2CrewMonitor from '../Phase2CrewMonitor';

// Custom hooks and components
import { useAgentMonitor } from './hooks/useAgentMonitor';
import { AgentList } from './components/AgentList';
import { AgentDetail } from './components/AgentDetail';
import { AgentStatus } from './components/AgentStatus';
import { AgentMetrics } from './components/AgentMetrics';
import { Agent } from './types';

const FlowCrewAgentMonitorContainer: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  
  const {
    data,
    isLoading,
    error,
    activeTab,
    refreshing,
    isStartingFlow,
    usePhase2Monitor,
    discoveryFlows,
    fetchMonitoringData,
    setActiveTab,
    togglePhase2Monitor,
    startFlow
  } = useAgentMonitor();

  const handleAgentSelect = (agent: Agent) => {
    setSelectedAgent(agent);
    setActiveTab('detail');
  };

  // Phase 2 Monitor fallback
  if (usePhase2Monitor) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
            <Bot className="h-6 w-6 text-blue-600" />
            <span>Agent Monitor (Phase 2)</span>
          </h2>
          <Button
            variant="outline"
            onClick={togglePhase2Monitor}
            className="flex items-center space-x-2"
          >
            <Settings className="h-4 w-4" />
            <span>Switch to Enhanced Monitor</span>
          </Button>
        </div>
        <Phase2CrewMonitor />
      </div>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Loading Agent Monitor</h3>
          <p className="text-gray-600">Fetching real-time agent and crew data...</p>
        </CardContent>
      </Card>
    );
  }

  const allCrews = data?.active_flows?.flatMap(flow => flow.crews) || [];
  const allAgents = allCrews.flatMap(crew => crew.agents);
  const activeAgents = allAgents.filter(agent => agent.status === 'active');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Bot className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Agent Monitor</h1>
            <p className="text-gray-600">
              Real-time monitoring of CrewAI agents and discovery flows
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Status indicators */}
          <div className="flex items-center space-x-2">
            <Badge variant="outline" className="bg-blue-50 text-blue-700">
              {data?.system_health?.total_flows || 0} Flows
            </Badge>
            <Badge variant="outline" className="bg-green-50 text-green-700">
              {activeAgents.length} Active Agents
            </Badge>
            <Badge variant="outline" className="bg-purple-50 text-purple-700">
              {allCrews.length} Crews
            </Badge>
          </div>
          
          {/* Action buttons */}
          <Button
            variant="outline"
            size="sm"
            onClick={fetchMonitoringData}
            disabled={refreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={togglePhase2Monitor}
            className="flex items-center space-x-2"
          >
            <Settings className="h-4 w-4" />
            <span>Phase 2 Monitor</span>
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertDescription className="text-yellow-800">
            <strong>Monitoring Notice:</strong> {error}
          </AlertDescription>
        </Alert>
      )}

      {/* System Health Quick View */}
      {data?.system_health && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className={`h-5 w-5 ${
                data.system_health.status === 'healthy' ? 'text-green-600' : 
                data.system_health.status === 'degraded' ? 'text-yellow-600' : 
                'text-red-600'
              }`} />
              <span>System Health</span>
              <Badge className={
                data.system_health.status === 'healthy' ? 'bg-green-100 text-green-800' :
                data.system_health.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }>
                {data.system_health.status.toUpperCase()}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {data.system_health.total_flows}
                </div>
                <div className="text-sm text-gray-600">Active Flows</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {data.system_health.active_crews}
                </div>
                <div className="text-sm text-gray-600">Available Crews</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">
                  {data.system_health.active_agents}
                </div>
                <div className="text-sm text-gray-600">Total Agents</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-600">
                  {activeAgents.length}
                </div>
                <div className="text-sm text-gray-600">Currently Active</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="agents" className="flex items-center space-x-2">
            <Users className="h-4 w-4" />
            <span>Agents</span>
          </TabsTrigger>
          <TabsTrigger value="detail" className="flex items-center space-x-2">
            <Eye className="h-4 w-4" />
            <span>Detail</span>
          </TabsTrigger>
          <TabsTrigger value="status" className="flex items-center space-x-2">
            <Activity className="h-4 w-4" />
            <span>Status</span>
          </TabsTrigger>
          <TabsTrigger value="metrics" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>Metrics</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-6">
          <AgentList
            crews={allCrews}
            onAgentSelect={handleAgentSelect}
            selectedAgentId={selectedAgent?.id}
          />
        </TabsContent>

        <TabsContent value="detail" className="space-y-6">
          <AgentDetail
            agent={selectedAgent}
            crewName={selectedAgent ? allCrews.find(crew => 
              crew.agents.some(agent => agent.id === selectedAgent.id)
            )?.name : undefined}
          />
        </TabsContent>

        <TabsContent value="status" className="space-y-6">
          <AgentStatus data={data} />
        </TabsContent>

        <TabsContent value="metrics" className="space-y-6">
          <AgentMetrics crews={allCrews} />
        </TabsContent>
      </Tabs>

      {/* Discovery Flows Info */}
      {discoveryFlows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5 text-blue-600" />
              <span>Active Discovery Flows</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {discoveryFlows.map((flow, index) => (
                <div key={flow.flow_id || index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <span className="font-medium">{flow.flow_id || 'Unknown Flow'}</span>
                    <span className="text-gray-600 ml-2">• {flow.current_phase || 'Unknown Phase'}</span>
                  </div>
                  <Badge variant="outline">
                    {flow.status || 'Unknown'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FlowCrewAgentMonitorContainer;